"""Parser para relatorios da XP Investimentos (PDF - Posicao Detalhada/Consolidada)."""

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
    """Extrai percentual de texto, ex: '42.56%' -> 42.56."""
    m = re.search(r'(-?[\d.]+)%', text)
    if m:
        try:
            return float(m.group(1))
        except ValueError:
            pass
    return 0.0


def _classify_tipo(categoria: str) -> str:
    """Classifica tipo do ativo baseado na categoria XP."""
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


def _extract_ticker(nome: str) -> str:
    """Extrai ticker de acoes (XXXX3, XXXX4, XXXX11, etc)."""
    m = re.search(r'\b([A-Z]{4}\d{1,2})\b', nome)
    return m.group(1) if m else ""


def parse_xp_pdf(file_path: str) -> InstitutionData:
    """Parseia relatorio XP Posicao Detalhada/Consolidada."""
    warnings.filterwarnings("ignore")

    with pdfplumber.open(file_path) as pdf:
        full_text = ""
        for page in pdf.pages:
            full_text += (page.extract_text() or "") + "\n"

    # ---- Metadados ----
    cliente = ""
    m = re.search(r'Cliente[:\s]*([A-Z][a-zA-Z\s]+?)(?:\s+Conta)', full_text)
    if m:
        cliente = m.group(1).strip()

    conta = ""
    m = re.search(r'Conta[:\s]*(\d{4,})', full_text)
    if m:
        conta = m.group(1)

    data_ref = ""
    m = re.search(r'refer[eê\x89]ncia[:\s]*(\d{2}/\d{2}/\d{4})', full_text, re.IGNORECASE)
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

    # ---- Patrimonio ----
    patrimonio = 0.0
    m = re.search(r'PATRIM[OÔ\x94]NIO(?:\s+TOTAL)?\s+(?:INVESTIMENTO\s+)?.*?R\$\s*([\d.,]+)', full_text, re.IGNORECASE)
    if m:
        patrimonio = _parse_br_number(m.group(1))
    if not patrimonio:
        m = re.search(r'PATRIM[OÔ\x94]NIO\s+TOTAL\s+R\$\s*([\d.,]+)', full_text, re.IGNORECASE)
        if m:
            patrimonio = _parse_br_number(m.group(1))

    # ---- Parse categorias e ativos ----
    ativos = []
    current_categoria = ""

    # Padroes de categoria no PDF XP:
    # "XX.X% Ações" ou "XX.XX% Fundos de investimento" com "R$ XXX.XXX,XX" abaixo
    # Sub-categorias: "XX.X% | Fundos de Renda Fixa Pós-Fixado"
    lines = full_text.split("\n")

    # Regex para categorias principais: "XX% Nome R$ valor" ou "XX.X% Nome"
    cat_pattern = re.compile(
        r'([\d.,]+)%\s+(.+?)$'
    )
    # Valor da categoria na linha seguinte ou mesma
    cat_valor_pattern = re.compile(r'R\$\s*([\d.,]+)')

    i = 0
    while i < len(lines):
        line = lines[i].strip()

        # Detecta categoria principal (ex: "0% Ações" ou "31.6% Fundos de investimento")
        cat_m = cat_pattern.match(line)
        if cat_m:
            pct = cat_m.group(1)
            nome_cat = cat_m.group(2).strip()
            # Filtra falsos positivos (linhas de dados numéricas)
            if any(kw in nome_cat.lower().replace("\xe7", "c").replace("\xe3", "a").replace("\xea", "e") for kw in [
                "acoes", "acao", "renda fixa", "fundo", "previd", "coe",
                "estruturad", "garantia", "custodia", "proventos", "saldo"
            ]):
                current_categoria = nome_cat
                # Pula categorias sem valor (0% ou garantia ou proventos ou saldo)
                if any(skip in current_categoria.lower().replace("\xe7", "c").replace("\xe3", "a") for skip in [
                    "garantia", "proventos", "saldo"
                ]):
                    i += 1
                    continue

            # Sub-categoria com pipe: "5.2% | Fundos de Renda Fixa Pós-Fixado"
            if "|" in nome_cat:
                sub = nome_cat.split("|", 1)[1].strip()
                current_categoria = sub

        # ---- Parse Acoes ----
        # "BPAC11 469 0 0 231 0 -700 0 R$ 41,82 42.56% R$ 59,62 R$ 0,00"
        acoes_m = re.match(
            r'^([A-Z]{4}\d{1,2})\s+(\d+)\s+.*?R\$\s*([\d.,]+)\s+([-\d.]+)%\s+R\$\s*([\d.,]+)\s+R\$\s*([\d.,]+)',
            line
        )
        if acoes_m and "acao" in current_categoria.lower().replace("\xe7", "c").replace("\xf5", "o").replace("\xe3", "a"):
            ticker = acoes_m.group(1)
            preco_medio = _parse_br_number(acoes_m.group(3))
            rent = float(acoes_m.group(4))
            cotacao = _parse_br_number(acoes_m.group(5))
            posicao = _parse_br_number(acoes_m.group(6))
            qtd = int(acoes_m.group(2))

            # Se posicao = 0 mas tem qtd em garantia/estruturado, calcula
            if posicao == 0 and cotacao > 0 and qtd > 0:
                # Pode estar em estruturado - valor ja contado la
                pass

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

        # Detecta "Custódia Remunerada" como categoria (aparece sem %)
        if "cust" in line.lower().replace("\xf3", "o") and "remunerada" in line.lower():
            current_categoria = "Custodia Remunerada"
            i += 1
            continue

        # ---- Parse Custodia Remunerada ----
        # "BPAC11 336,00 04/03/2026 R$ 59,62 R$ 20.032,32"
        cust_m = re.match(
            r'^([A-Z]{4}\d{1,2})\s+([\d.,]+)\s+(\d{2}/\d{2}/\d{4})\s+R\$\s*([\d.,]+)\s+R\$\s*([\d.,]+)',
            line
        )
        if cust_m and ("cust" in current_categoria.lower() or "papel" not in line.lower()):
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

        # ---- Parse Renda Fixa (CRI, CDB, LCA, etc) ----
        # "CRI JHSF - MAI/2030 29/05/2025 15/05/2030 15/05/2030 105,00% CDI 6 0 0 R$ 6.000,00 R$ 6.000,00 R$ 6.255,28 R$ 6.255,28"
        rf_m = re.match(
            r'^(CRI|CRA|CDB|LCA|LCI|LF|DEB)\s+(.+?)\s+(\d{2}/\d{2}/\d{4})\s+(\d{2}/\d{2}/\d{4})\s+(\d{2}/\d{2}/\d{4})\s+([\d.,]+%?\s*\w*)',
            line
        )
        if rf_m:
            tipo_rf = rf_m.group(1)
            nome_rf = f"{tipo_rf} {rf_m.group(2).strip()}"
            vencimento = rf_m.group(4)
            taxa = rf_m.group(6).strip()
            # Pega valores R$ da linha
            r_values = re.findall(r'R\$\s*([\d.,]+)', line)
            valor_liquido = _parse_br_number(r_values[-1]) if r_values else 0.0

            indexador = ""
            if "CDI" in taxa.upper():
                indexador = "CDI"
            elif "IPCA" in taxa.upper():
                indexador = "IPCA"
            elif "PRE" in taxa.upper() or "PRÉ" in taxa.upper():
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

        # ---- Parse Fundos ----
        # "Trend Cash CIC de Classes RF Simples RL 04/03/2026 148.8072402 169,75 R$ 0,00 R$ 25.259,54 R$ 25.182,42"
        # Pattern: nome data_cota valor_cota qtd_cotas em_cotizacao posicao valor_liquido
        fund_m = re.match(
            r'^(.+?)\s+(\d{2}/\d{2}/\d{4})\s+([\d.]+)\s+([\d.,]+)\s+R\$\s*([\d.,]+)\s+R\$\s*([\d.,]+)(?:\s+R\$\s*([\d.,]+))?',
            line
        )
        if fund_m and "fundo" in current_categoria.lower().replace("\xe3", "a"):
            nome_fundo = fund_m.group(1).strip()
            posicao = _parse_br_number(fund_m.group(6))
            valor_liq = _parse_br_number(fund_m.group(7)) if fund_m.group(7) else posicao

            tipo = _classify_tipo(current_categoria)
            # Refina tipo pelo nome do fundo
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

        # ---- Parse Previdencia ----
        # "JGP Crédito Prev Advisory XP Seg FIC RF CP 02/03/2026 189.3789645 636,40 VGBL Regressivo R$ 120.520,23 -"
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

        # ---- Parse COE ----
        # COE pode vir em 2 linhas:
        # Linha 1: "XP Brasil Soberano 2030 RF IPCA - Cupom Semestral -"
        # Linha 2: "BANCO XP S.A. 16/09/2025 30/12/2030 24000 R$ 1,03 R$ 24.000,00 R$ 24.770,35"
        # Ou tudo numa linha
        if "coe" in current_categoria.lower():
            # Tenta match da linha 2 (com BANCO)
            coe_m2 = re.match(
                r'^(BANCO\s+\w+\s+S\.?A\.?)\s+(\d{2}/\d{2}/\d{4})\s+(\d{2}/\d{2}/\d{4})\s+(\d+)\s+R\$\s*([\d.,]+)\s+R\$\s*([\d.,]+)\s+R\$\s*([\d.,]+)',
                line
            )
            if coe_m2:
                emissor = coe_m2.group(1).strip()
                vencimento = coe_m2.group(3)
                posicao = _parse_br_number(coe_m2.group(7))
                # Nome do COE esta na linha anterior
                nome_coe = lines[i - 1].strip() if i > 0 else "COE"
                # Limpa nome
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

        # ---- Parse Produtos Estruturados (Collar) ----
        # Detecta bloco: "XX.X% | Collar UI - SUZB3 R$ 16.890,00"
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

    # Recalcula alocacao
    if patrimonio > 0:
        for a in ativos:
            a.alocacao_pct = round(a.saldo_bruto / patrimonio * 100, 2)

    # Se nao achou patrimonio mas tem ativos, soma
    if not patrimonio and ativos:
        patrimonio = sum(a.saldo_bruto for a in ativos)

    # Distribuicao por tipo
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
        rent_carteira_mes=0.0,
        rent_carteira_ano=0.0,
        rent_carteira_12m=0.0,
        cdi_mes=0.0,
        cdi_ano=0.0,
        perfil_investidor=perfil,
        ativos=ativos,
        distribuicao_tipo=dist_tipo,
    )
