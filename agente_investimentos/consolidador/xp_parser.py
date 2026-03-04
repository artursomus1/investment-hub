"""Parser para relatorios da XP Investimentos (PDF).

Suporta dois formatos:
1. Posicao Detalhada (formato antigo com categorias XX% + linhas por tipo)
2. XPerformance (tabela uniforme: Estrategia | Saldo Bruto | Qtd | %Aloc | Rent | %CDI)
"""

import re
import warnings
from typing import List

import pdfplumber

from agente_investimentos.consolidador.models import ParsedAssetInst, InstitutionData


def _parse_br_number(text: str) -> float:
    """Converte numero BR '1.234,56' para float. Aceita negativo '-R$ 1.234'."""
    if not text or text.strip() in ("-", "", "None"):
        return 0.0
    text = text.strip().replace("R$", "").strip()
    neg = text.startswith("-")
    text = text.lstrip("-").strip()
    text = text.replace(".", "").replace(",", ".")
    try:
        val = float(text)
        return -val if neg else val
    except ValueError:
        return 0.0


def _extract_pct(text: str) -> float:
    """Extrai percentual de texto, ex: '42.56%' -> 42.56, '0,35%' -> 0.35."""
    if not text or text.strip() == "-":
        return 0.0
    m = re.search(r'(-?[\d.,]+)%', text)
    if m:
        return _parse_br_number(m.group(1))
    return 0.0


def _extract_ticker(nome: str) -> str:
    """Extrai ticker de acoes (XXXX3, XXXX4, XXXX11, etc)."""
    m = re.search(r'\b([A-Z]{4}\d{1,2})\b', nome)
    return m.group(1) if m else ""


def _classify_tipo_xperf(estrategia: str, nome: str) -> str:
    """Classifica tipo do ativo para formato XPerformance."""
    cat = estrategia.lower()
    nome_up = nome.upper()

    if "fixado" in cat or "pos" in cat:
        # LCA, LCI, CDB sao renda fixa; FIIs listados como AZQI11 sao FII
        if any(k in nome_up for k in ("FII", "FIP IE", "INFRA YIELD")):
            return "FII"
        return "Renda Fixa"
    if "infla" in cat:
        if any(k in nome_up for k in ("FII", "LAJE", "CORPORAT", "IMOBILI")):
            return "FII"
        return "Renda Fixa"
    if "renda vari" in cat or "variavel" in cat:
        return "Acao"
    if "alternativ" in cat:
        if any(k in nome_up for k in ("FII", "IMOBILI")):
            return "FII"
        if any(k in nome_up for k in ("FIP", "PRIVATE EQUITY", "CAPITAL PARTNERS")):
            return "Multimercado"
        return "Multimercado"
    if "renda fixa global" in cat:
        return "Renda Fixa"
    if "fundos listados" in cat or "listado" in cat:
        return "FII"
    if "previd" in cat:
        return "Previdencia"
    if "coe" in cat:
        return "Renda Fixa"
    if "estruturad" in cat:
        return "Op. Estruturadas"
    return "Renda Fixa"


def _classify_tipo(categoria: str) -> str:
    """Classifica tipo do ativo baseado na categoria XP (formato Posicao Detalhada)."""
    cat = categoria.lower()
    if "acao" in cat or "acoes" in cat or "a\xe7" in cat:
        return "Acao"
    if "renda fixa" in cat or "cri" in cat or "cra" in cat or "cdb" in cat or "lca" in cat:
        return "Renda Fixa"
    if "fundo" in cat:
        if "infla" in cat or "imobili" in cat or "fii" in cat:
            return "FII"
        if "alternativ" in cat:
            return "Multimercado"
        return "Renda Fixa"
    if "previd" in cat:
        return "Previdencia"
    if "coe" in cat:
        return "Renda Fixa"
    if "estruturad" in cat:
        return "Op. Estruturadas"
    if "custodia" in cat:
        return "Renda Fixa"
    return "Renda Fixa"


# ============================================================
# XPerformance format parser
# ============================================================

# Known category names in XPerformance PDF
_XPERF_CATEGORIES = [
    "Pos Fixado", "Pos-Fixado", "Pos fixado",
    "Inflacao", "Inflacaoo",
    "Renda Variavel Brasil", "Renda Vari",
    "Alternativo",
    "Renda Fixa Global",
    "Fundos Listados",
    "Previdencia", "Previd",
    "COE",
]


def _is_xperf_category_line(line: str) -> bool:
    """Check if line is a category line (has Qtd = '-')."""
    # Category pattern: NAME R$ VALUE - %ALOC RENT ...
    # The '-' after value distinguishes categories from assets
    m = re.search(r'R\$\s*[\d.,]+\s+-\s+[\d.,]+%', line)
    return bool(m)


def _is_name_suffix(line: str) -> bool:
    """Check if line is just a trailing suffix of a fund name (e.g. 'RL', 'FIC FI RL', 'Multiest')."""
    if not line or len(line) > 40:
        return False
    # No R$, no %, short text = likely a suffix
    if "R$" in line or "%" in line:
        return False
    # Must not start with a number or be a known category
    if re.match(r'^\d', line):
        return False
    return True


def _parse_xperf_format(full_text: str) -> List[ParsedAssetInst]:
    """Parse XPerformance format PDF."""
    ativos = []
    lines = full_text.split("\n")
    current_categoria = ""

    # Regex for asset line: NAME R$ SALDO QTD %ALOC RENT_MES %CDI RENT_ANO %CDI RENT_24M %CDI
    asset_pattern = re.compile(
        r'^(.+?)\s+R\$\s*([\d.,]+)\s+([\d.,-]+)\s+([\d.,]+)%'
        r'\s+(-?[\d.,]+|-)%?\s+(-?[\d.,]+|-)%?'
        r'\s+(-?[\d.,]+|-)%?\s+(-?[\d.,]+|-)%?'
    )

    # Category pattern: same but QTD = '-'
    cat_pattern = re.compile(
        r'^(.+?)\s+R\$\s*([\d.,]+)\s+-\s+([\d.,]+)%'
    )

    # Regex patterns for header/footer lines (must match at word boundaries, not substrings)
    _SKIP_PATTERNS = [
        re.compile(r'^estrat.gia\s+saldo\s+bruto', re.IGNORECASE),
        re.compile(r'saldo\s+bruto\s+qtd', re.IGNORECASE),
        re.compile(r'relat.rio\s+informativo', re.IGNORECASE),
        re.compile(r'precifica..o\s+de\s+renda', re.IGNORECASE),
        re.compile(r'^m.s\s+atual\s+ano', re.IGNORECASE),
        re.compile(r'^\s*%\s*aloc', re.IGNORECASE),
        re.compile(r'24\s+meses', re.IGNORECASE),
    ]

    i = 0
    in_detail_section = False

    while i < len(lines):
        line = lines[i].strip()

        # Normalize for header detection
        line_lower = line.lower().replace("\xc3\xa9", "e").replace("\xe9", "e").replace("\xea", "e").replace("\xc3\xaa", "e").replace("\xc3\xa3", "a").replace("\xe3", "a").replace("\xc3\xa7", "c").replace("\xe7", "c").replace("\xc3\xb3", "o").replace("\xf3", "o")

        # Detect start of POSICAO DETALHADA section
        if "detalhada dos ativos" in line_lower:
            in_detail_section = True
            i += 1
            continue

        # Skip header/footer lines
        if any(p.search(line_lower) for p in _SKIP_PATTERNS):
            if "relat" in line_lower and "informativo" in line_lower:
                in_detail_section = False
            i += 1
            continue

        if not in_detail_section:
            if "posicao detalhada" in line_lower or "posiao detalhada" in line_lower:
                in_detail_section = True
            i += 1
            continue

        # Skip Aviso/disclaimer
        if line.startswith("*"):
            i += 1
            continue

        # Skip empty
        if not line:
            i += 1
            continue

        # Check if this is a category line (QTD = '-')
        cat_m = cat_pattern.match(line)
        if cat_m and _is_xperf_category_line(line):
            current_categoria = cat_m.group(1).strip()
            i += 1
            continue

        # Try to match asset line (all on one line)
        asset_m = asset_pattern.match(line)
        if asset_m:
            nome = asset_m.group(1).strip()
            saldo = _parse_br_number(asset_m.group(2))
            aloc = _extract_pct(asset_m.group(4) + "%")
            rent_mes = _extract_pct(asset_m.group(5) + "%") if asset_m.group(5) != "-" else 0.0
            rent_ano = _extract_pct(asset_m.group(7) + "%") if asset_m.group(7) != "-" else 0.0

            # Skip options (CALL/PUT) with 0 value
            if saldo <= 0:
                i += 1
                continue

            ticker = _extract_ticker(nome)
            tipo = _classify_tipo_xperf(current_categoria, nome)

            all_pcts = re.findall(r'(-?[\d.,]+)%', line)
            rent_24m = _extract_pct(all_pcts[4] + "%") if len(all_pcts) >= 5 else 0.0

            ativos.append(ParsedAssetInst(
                nome=nome, ticker=ticker, tipo=tipo,
                subtipo=current_categoria or tipo,
                saldo_bruto=saldo, saldo_liquido=saldo, impostos=0.0,
                alocacao_pct=round(aloc, 2),
                rent_mes=rent_mes, rent_ano=rent_ano, rent_12m=rent_24m,
                indexador="", taxa="", vencimento="", emissor="",
                instituicao="XP",
            ))

            # Skip trailing name suffix lines (e.g., "RL", "FIC FI RL", "Multiest")
            while i + 1 < len(lines) and _is_name_suffix(lines[i + 1].strip()):
                i += 1

            i += 1
            continue

        # Check if this is a multi-line fund name (name on this line, R$ on next)
        if line and "R$" not in line and len(line) > 3:
            # Look ahead for R$ values line
            next_idx = i + 1
            while next_idx < len(lines) and next_idx <= i + 2:
                next_line = lines[next_idx].strip()
                if not next_line:
                    next_idx += 1
                    continue
                if "R$" in next_line:
                    # Try combined match
                    combined = line + " " + next_line
                    combined_m = asset_pattern.match(combined)

                    # Also check if the R$ line alone starts with R$
                    if not combined_m and next_line.startswith("R$"):
                        # Name is on current line, values start with R$ on next
                        val_m = re.match(
                            r'^R\$\s*([\d.,]+)\s+([\d.,-]+)\s+([\d.,]+)%'
                            r'\s+(-?[\d.,]+|-)%?\s+(-?[\d.,]+|-)%?'
                            r'\s+(-?[\d.,]+|-)%?\s+(-?[\d.,]+|-)%?',
                            next_line
                        )
                        if val_m:
                            nome = line
                            saldo = _parse_br_number(val_m.group(1))
                            aloc = _extract_pct(val_m.group(3) + "%")
                            rent_mes = _extract_pct(val_m.group(4) + "%") if val_m.group(4) != "-" else 0.0
                            rent_ano = _extract_pct(val_m.group(6) + "%") if val_m.group(6) != "-" else 0.0

                            if saldo > 0:
                                ticker = _extract_ticker(nome)
                                tipo = _classify_tipo_xperf(current_categoria, nome)
                                all_pcts = re.findall(r'(-?[\d.,]+)%', next_line)
                                rent_24m = _extract_pct(all_pcts[3] + "%") if len(all_pcts) >= 4 else 0.0

                                ativos.append(ParsedAssetInst(
                                    nome=nome, ticker=ticker, tipo=tipo,
                                    subtipo=current_categoria or tipo,
                                    saldo_bruto=saldo, saldo_liquido=saldo, impostos=0.0,
                                    alocacao_pct=round(aloc, 2),
                                    rent_mes=rent_mes, rent_ano=rent_ano, rent_12m=rent_24m,
                                    indexador="", taxa="", vencimento="", emissor="",
                                    instituicao="XP",
                                ))

                            # Skip suffix lines after the values line
                            i = next_idx
                            while i + 1 < len(lines) and _is_name_suffix(lines[i + 1].strip()):
                                i += 1
                            i += 1
                            break

                    if combined_m:
                        nome = combined_m.group(1).strip()
                        saldo = _parse_br_number(combined_m.group(2))
                        aloc = _extract_pct(combined_m.group(4) + "%")
                        rent_mes = _extract_pct(combined_m.group(5) + "%") if combined_m.group(5) != "-" else 0.0
                        rent_ano = _extract_pct(combined_m.group(7) + "%") if combined_m.group(7) != "-" else 0.0

                        if saldo > 0:
                            ticker = _extract_ticker(nome)
                            tipo = _classify_tipo_xperf(current_categoria, nome)
                            all_pcts = re.findall(r'(-?[\d.,]+)%', combined)
                            rent_24m = _extract_pct(all_pcts[4] + "%") if len(all_pcts) >= 5 else 0.0

                            ativos.append(ParsedAssetInst(
                                nome=nome, ticker=ticker, tipo=tipo,
                                subtipo=current_categoria or tipo,
                                saldo_bruto=saldo, saldo_liquido=saldo, impostos=0.0,
                                alocacao_pct=round(aloc, 2),
                                rent_mes=rent_mes, rent_ano=rent_ano, rent_12m=rent_24m,
                                indexador="", taxa="", vencimento="", emissor="",
                                instituicao="XP",
                            ))

                        # Skip suffix lines
                        i = next_idx
                        while i + 1 < len(lines) and _is_name_suffix(lines[i + 1].strip()):
                            i += 1
                        i += 1
                        break
                    break
                else:
                    next_idx += 1
            else:
                i += 1
            continue

        i += 1

    return ativos


# ============================================================
# Posicao Detalhada format parser (original)
# ============================================================

def _parse_posicao_detalhada(full_text: str, lines: list) -> List[ParsedAssetInst]:
    """Parse Posicao Detalhada format (original XP format)."""
    ativos = []
    current_categoria = ""

    cat_pattern = re.compile(r'([\d.,]+)%\s+(.+?)$')

    i = 0
    while i < len(lines):
        line = lines[i].strip()

        # Detecta categoria principal
        cat_m = cat_pattern.match(line)
        if cat_m:
            pct = cat_m.group(1)
            nome_cat = cat_m.group(2).strip()
            if any(kw in nome_cat.lower().replace("\xe7", "c").replace("\xe3", "a").replace("\xea", "e") for kw in [
                "acoes", "acao", "renda fixa", "fundo", "previd", "coe",
                "estruturad", "garantia", "custodia", "proventos", "saldo"
            ]):
                current_categoria = nome_cat
                if any(skip in current_categoria.lower().replace("\xe7", "c").replace("\xe3", "a") for skip in [
                    "garantia", "proventos", "saldo"
                ]):
                    i += 1
                    continue
            if "|" in nome_cat:
                sub = nome_cat.split("|", 1)[1].strip()
                current_categoria = sub

        # Parse Acoes
        acoes_m = re.match(
            r'^([A-Z]{4}\d{1,2})\s+(\d+)\s+.*?R\$\s*([\d.,]+)\s+([-\d.]+)%\s+R\$\s*([\d.,]+)\s+R\$\s*([\d.,]+)',
            line
        )
        if acoes_m and "acao" in current_categoria.lower().replace("\xe7", "c").replace("\xf5", "o").replace("\xe3", "a"):
            ticker = acoes_m.group(1)
            rent = float(acoes_m.group(4))
            posicao = _parse_br_number(acoes_m.group(6))
            if posicao > 0:
                ativos.append(ParsedAssetInst(
                    nome=ticker, ticker=ticker, tipo="Acao", subtipo="Acao",
                    saldo_bruto=posicao, saldo_liquido=posicao, impostos=0.0,
                    alocacao_pct=0.0, rent_mes=0.0, rent_ano=rent, rent_12m=0.0,
                    indexador="", taxa="", vencimento="", emissor="",
                    instituicao="XP",
                ))
            i += 1
            continue

        # Custodia Remunerada
        if "cust" in line.lower().replace("\xf3", "o") and "remunerada" in line.lower():
            current_categoria = "Custodia Remunerada"
            i += 1
            continue

        cust_m = re.match(
            r'^([A-Z]{4}\d{1,2})\s+([\d.,]+)\s+(\d{2}/\d{2}/\d{4})\s+R\$\s*([\d.,]+)\s+R\$\s*([\d.,]+)',
            line
        )
        if cust_m and "cust" in current_categoria.lower():
            ticker = cust_m.group(1)
            financeiro = _parse_br_number(cust_m.group(5))
            if financeiro > 0:
                ativos.append(ParsedAssetInst(
                    nome=f"{ticker} (Custodia)", ticker=ticker, tipo="Renda Fixa",
                    subtipo="Custodia Remunerada",
                    saldo_bruto=financeiro, saldo_liquido=financeiro, impostos=0.0,
                    alocacao_pct=0.0, rent_mes=0.0, rent_ano=0.0, rent_12m=0.0,
                    indexador="", taxa="", vencimento=cust_m.group(3), emissor="",
                    instituicao="XP",
                ))
            i += 1
            continue

        # Renda Fixa
        rf_m = re.match(
            r'^(CRI|CRA|CDB|LCA|LCI|LF|DEB)\s+(.+?)\s+(\d{2}/\d{2}/\d{4})\s+(\d{2}/\d{2}/\d{4})\s+(\d{2}/\d{2}/\d{4})\s+([\d.,]+%?\s*\w*)',
            line
        )
        if rf_m:
            tipo_rf = rf_m.group(1)
            nome_rf = f"{tipo_rf} {rf_m.group(2).strip()}"
            vencimento = rf_m.group(4)
            taxa = rf_m.group(6).strip()
            r_values = re.findall(r'R\$\s*([\d.,]+)', line)
            valor_liquido = _parse_br_number(r_values[-1]) if r_values else 0.0
            indexador = ""
            if "CDI" in taxa.upper():
                indexador = "CDI"
            elif "IPCA" in taxa.upper():
                indexador = "IPCA"
            elif "PRE" in taxa.upper():
                indexador = "PRE"
            if valor_liquido > 0:
                ativos.append(ParsedAssetInst(
                    nome=nome_rf, ticker="", tipo="Renda Fixa", subtipo=tipo_rf,
                    saldo_bruto=valor_liquido, saldo_liquido=valor_liquido, impostos=0.0,
                    alocacao_pct=0.0, rent_mes=0.0, rent_ano=0.0, rent_12m=0.0,
                    indexador=indexador, taxa=taxa, vencimento=vencimento, emissor="",
                    instituicao="XP",
                ))
            i += 1
            continue

        # Fundos
        fund_m = re.match(
            r'^(.+?)\s+(\d{2}/\d{2}/\d{4})\s+([\d.]+)\s+([\d.,]+)\s+R\$\s*([\d.,]+)\s+R\$\s*([\d.,]+)(?:\s+R\$\s*([\d.,]+))?',
            line
        )
        if fund_m and "fundo" in current_categoria.lower().replace("\xe3", "a"):
            nome_fundo = fund_m.group(1).strip()
            posicao = _parse_br_number(fund_m.group(6))
            valor_liq = _parse_br_number(fund_m.group(7)) if fund_m.group(7) else posicao
            tipo = _classify_tipo(current_categoria)
            nome_up = nome_fundo.upper()
            if any(k in nome_up for k in ("FII", "IMOBILI", "MALL", "LAJE", "CORPORAT")):
                tipo = "FII"
            elif any(k in nome_up for k in ("MULTI", "MACRO", "QUANT", "ALTERNATIV")):
                tipo = "Multimercado"
            if posicao > 0:
                ativos.append(ParsedAssetInst(
                    nome=nome_fundo, ticker="", tipo=tipo, subtipo="Fundo",
                    saldo_bruto=posicao, saldo_liquido=valor_liq, impostos=0.0,
                    alocacao_pct=0.0, rent_mes=0.0, rent_ano=0.0, rent_12m=0.0,
                    indexador="", taxa="", vencimento="", emissor="",
                    instituicao="XP",
                ))
            i += 1
            continue

        # Previdencia
        prev_m = re.match(
            r'^(.+?)\s+(\d{2}/\d{2}/\d{4})\s+([\d.]+)\s+([\d.,]+)\s+(VGBL|PGBL)\s+(\w+)\s+R\$\s*([\d.,]+)',
            line
        )
        if prev_m:
            nome_prev = prev_m.group(1).strip()
            plano = prev_m.group(5)
            tributacao = prev_m.group(6)
            posicao = _parse_br_number(prev_m.group(7))
            if posicao > 0:
                ativos.append(ParsedAssetInst(
                    nome=f"{nome_prev} ({plano})", ticker="", tipo="Previdencia",
                    subtipo=f"{plano} {tributacao}",
                    saldo_bruto=posicao, saldo_liquido=posicao, impostos=0.0,
                    alocacao_pct=0.0, rent_mes=0.0, rent_ano=0.0, rent_12m=0.0,
                    indexador="", taxa="", vencimento="", emissor="",
                    instituicao="XP",
                ))
            i += 1
            continue

        # COE
        if "coe" in current_categoria.lower():
            coe_m2 = re.match(
                r'^(BANCO\s+\w+\s+S\.?A\.?)\s+(\d{2}/\d{2}/\d{4})\s+(\d{2}/\d{2}/\d{4})\s+(\d+)\s+R\$\s*([\d.,]+)\s+R\$\s*([\d.,]+)\s+R\$\s*([\d.,]+)',
                line
            )
            if coe_m2:
                emissor = coe_m2.group(1).strip()
                vencimento = coe_m2.group(3)
                posicao = _parse_br_number(coe_m2.group(7))
                nome_coe = lines[i - 1].strip() if i > 0 else "COE"
                nome_coe = nome_coe.rstrip(" -").strip()
                if posicao > 0:
                    ativos.append(ParsedAssetInst(
                        nome=f"COE {nome_coe}", ticker="", tipo="Renda Fixa", subtipo="COE",
                        saldo_bruto=posicao, saldo_liquido=posicao, impostos=0.0,
                        alocacao_pct=0.0, rent_mes=0.0, rent_ano=0.0, rent_12m=0.0,
                        indexador="", taxa="", vencimento=vencimento, emissor=emissor,
                        instituicao="XP",
                    ))
                i += 1
                continue

        # Collar / Produtos Estruturados
        collar_m = re.match(
            r'^[\d.,]+%\s*\|\s*(Collar.+?)\s+R\$\s*([\d.,]+)',
            line, re.IGNORECASE,
        )
        if collar_m:
            nome_estr = collar_m.group(1).strip()
            posicao = _parse_br_number(collar_m.group(2))
            ticker = _extract_ticker(nome_estr)
            if posicao > 0:
                ativos.append(ParsedAssetInst(
                    nome=nome_estr, ticker=ticker, tipo="Op. Estruturadas",
                    subtipo="Collar",
                    saldo_bruto=posicao, saldo_liquido=posicao, impostos=0.0,
                    alocacao_pct=0.0, rent_mes=0.0, rent_ano=0.0, rent_12m=0.0,
                    indexador="", taxa="", vencimento="", emissor="",
                    instituicao="XP",
                ))
            i += 1
            continue

        i += 1

    return ativos


# ============================================================
# Main entry point
# ============================================================

def parse_xp_pdf(file_path: str) -> InstitutionData:
    """Parseia relatorio XP (Posicao Detalhada ou XPerformance)."""
    warnings.filterwarnings("ignore")

    with pdfplumber.open(file_path) as pdf:
        full_text = ""
        for page in pdf.pages:
            full_text += (page.extract_text() or "") + "\n"

    # ---- Detect format ----
    text_upper = full_text.upper()
    # XPerformance has "RENTABILIDADE POR CLASSE" and uniform table
    is_xperf = ("RENTABILIDADE POR CLASSE" in text_upper
                or "ESTRATEGIA" in text_upper.replace("\xc9", "E")
                or ("XPERFORMANCE" in text_upper)
                or ("MES ATUAL" in text_upper.replace("\xca", "E") and "24 MESES" in text_upper))

    # ---- Metadados ----
    cliente = ""
    m = re.search(r'Cliente[:\s]*([A-Z][a-zA-Z\s]+?)(?:\s+Conta)', full_text)
    if m:
        cliente = m.group(1).strip()

    conta = ""
    m = re.search(r'Conta[:\s]*(\d{4,})', full_text)
    if not m:
        m = re.search(r'^.*?Conta\s+.*?(\d{5,})', full_text, re.MULTILINE)
    if m:
        conta = m.group(1)

    data_ref = ""
    m = re.search(r'[Rr]efer[eê\x89]ncia[:\s]*(\d{2}/\d{2}/\d{4})', full_text)
    if m:
        data_ref = m.group(1)

    perfil = ""
    m = re.search(r'Perfil[:\s]*(Conservador|Moderado|Moderada|Agressivo|Arrojado)', full_text, re.IGNORECASE)
    if m:
        perfil = m.group(1).strip()

    assessor = ""
    m = re.search(r'Assessor(?:ia)?[:\s]*([A-Z][a-zA-Z\s]+?)(?:\(|$|\n)', full_text)
    if m:
        assessor = m.group(1).strip()

    # ---- Patrimonio (try to find explicitly) ----
    patrimonio = 0.0
    m = re.search(r'PATRIM[OÔ\x94]NIO(?:\s+TOTAL)?\s+(?:INVESTIMENTO\s+)?.*?R\$\s*([\d.,]+)', full_text, re.IGNORECASE)
    if m:
        patrimonio = _parse_br_number(m.group(1))

    # ---- Parse ativos ----
    lines = full_text.split("\n")

    if is_xperf:
        ativos = _parse_xperf_format(full_text)
    else:
        ativos = _parse_posicao_detalhada(full_text, lines)

    # ---- Calculate patrimonio if not found ----
    if not patrimonio and ativos:
        patrimonio = sum(a.saldo_bruto for a in ativos)

    # ---- Recalculate allocation ----
    if patrimonio > 0:
        for a in ativos:
            if a.alocacao_pct == 0:
                a.alocacao_pct = round(a.saldo_bruto / patrimonio * 100, 2)

    # ---- Rentabilidade ponderada ----
    rent_mes = 0.0
    rent_ano = 0.0
    if ativos and patrimonio > 0:
        rent_mes = sum(a.rent_mes * a.saldo_bruto for a in ativos) / patrimonio
        rent_ano = sum(a.rent_ano * a.saldo_bruto for a in ativos) / patrimonio

    # ---- Distribuicao por tipo ----
    dist_tipo = {}
    for a in ativos:
        dist_tipo[a.tipo] = dist_tipo.get(a.tipo, 0.0) + a.alocacao_pct

    return InstitutionData(
        nome="XP",
        cliente=cliente,
        conta=conta,
        data_referencia=data_ref,
        patrimonio_bruto=patrimonio,
        patrimonio_liquido=patrimonio,
        impostos_totais=0.0,
        rent_carteira_mes=round(rent_mes, 2),
        rent_carteira_ano=round(rent_ano, 2),
        rent_carteira_12m=0.0,
        cdi_mes=0.0,
        cdi_ano=0.0,
        perfil_investidor=perfil,
        ativos=ativos,
        distribuicao_tipo=dist_tipo,
    )
