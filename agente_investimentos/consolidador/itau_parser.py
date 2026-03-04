"""Parser para relatorios do Itau Personnalite (PDF - Posicao Consolidada).

Usa extract_tables() do pdfplumber para extrair dados estruturados.

Estrutura do PDF Itau:
- Tabelas de categoria (1 row): ['', 'Categoria', 'R$ rendimento', 'XX,XX%', 'R$ valor']
- Tabelas de produtos (N rows): [nome_multiline, rent_mes, rent_mes_ant, rent_ano, ...]
  com valor investido na ultima coluna
- Linha 'total investido' com R$ total
"""

import re
from typing import List, Tuple

import pdfplumber

from agente_investimentos.consolidador.models import ParsedAssetInst, InstitutionData


def _parse_br_number(text: str) -> float:
    """Converte numero BR '1.234,56' para float."""
    if not text or text.strip() in ("-", "", "None"):
        return 0.0
    # Remove R$ e espacos
    text = text.strip().replace("R$", "").strip()
    text = text.replace(".", "").replace(",", ".")
    try:
        return float(text)
    except ValueError:
        return 0.0


def _extract_pct(cell: str) -> float:
    """Extrai primeiro percentual de uma celula. Ex: 'R$ 49,99\\n0,05%' -> 0.05."""
    if not cell:
        return 0.0
    m = re.search(r'(-?[\d.,]+)%', cell)
    if m:
        return _parse_br_number(m.group(1))
    return 0.0


def _clean_name(raw: str) -> str:
    """Limpa nome de produto extraido de celula multiline."""
    if not raw:
        return ""
    # Remove newlines, junta e limpa
    name = raw.replace("\n", " ").strip()
    name = re.sub(r'\s+', ' ', name)
    # Corrige caracteres comuns de encoding do PDF
    _REPLACEMENTS = {
        "\x89": "e", "\x8e": "e", "\x8f": "e",
        "\x9f": "u", "\x9c": "o", "\x82": "e",
        "\x83": "a", "\x84": "a", "\x85": "a",
        "\x87": "c", "\x88": "e", "\x93": "o",
        "\x94": "o", "\x95": "o", "\x96": "-",
        "\x97": "-", "\xa0": " ", "\xad": "",
    }
    for old, new in _REPLACEMENTS.items():
        name = name.replace(old, new)
    return name


def _extract_ticker(nome: str) -> str:
    """Extrai ticker entre parenteses, ex: (KNCR11)."""
    m = re.search(r'\(([A-Z]{4}\d{1,2})\)', nome)
    return m.group(1) if m else ""


def _extract_vencimento(nome: str) -> str:
    """Extrai data de vencimento, ex: '06/04/2026'."""
    m = re.search(r'(\d{2}/\d{2}/\d{4})', nome)
    return m.group(1) if m else ""


def _extract_taxa(nome: str) -> str:
    """Extrai taxa percentual do nome, ex: 'PRE 11.54%'."""
    m = re.search(r'(\d+[.,]\d+%)', nome)
    return m.group(1) if m else ""


def _extract_indexador(nome: str) -> str:
    """Detecta indexador pelo nome."""
    up = nome.upper()
    if "CDI" in up:
        return "CDI"
    if "IPCA" in up:
        return "IPCA"
    if "PRE" in up or "PRÉ" in up:
        return "PRE"
    if "SELIC" in up:
        return "SELIC"
    return ""


def _classify_tipo(categoria: str, nome: str) -> str:
    """Classifica tipo do ativo."""
    cat = categoria.lower()
    up = nome.upper()

    if "imobili" in cat or "FII" in up or "IFRI" in up:
        return "FII"
    if "fundo" in cat:
        if any(k in up for k in ("FII", "IFRI", "IMOBILI", "KNCR", "HGLG", "XPLG", "KNRI")):
            return "FII"
        if any(k in up for k in ("MULTIMERCADO", "MACRO", "QUANT")):
            return "Multimercado"
        return "Renda Fixa"
    if "cdb" in cat or "renda fixa" in cat or "estruturado" in cat:
        return "Renda Fixa"
    if "poupan" in cat:
        return "Renda Fixa"
    if "previd" in cat:
        return "Previdencia"
    if "tesouro" in cat:
        return "Renda Fixa"
    if "acoes" in cat or "acao" in cat:
        return "Acao"
    return "Renda Fixa"


def _is_category_table(table: list) -> Tuple[bool, str, float, float]:
    """Verifica se tabela e uma linha de categoria.

    Formato: ['', 'Categoria', 'R$ rendimento', 'XX,XX%', 'R$ valor']
    Retorna: (is_category, nome_categoria, distribuicao_pct, valor_investido)
    """
    if not table or len(table) != 1:
        return False, "", 0.0, 0.0

    row = table[0]
    if len(row) < 4:
        return False, "", 0.0, 0.0

    # Celula 1 (ou 0) deve ter nome da categoria
    cat_cell = (row[1] or "").strip() if len(row) > 1 else ""
    if not cat_cell:
        cat_cell = (row[0] or "").strip()

    _CAT_KEYWORDS = [
        "Fundos de Investimento", "Investimentos Imobili",
        "CDB, Renda Fixa", "Poupan", "Previd", "Tesouro", "Acoes",
    ]

    is_cat = any(kw.lower() in cat_cell.lower().replace("ã", "a").replace("ç", "c").replace("õ", "o") for kw in _CAT_KEYWORDS)
    if not is_cat:
        return False, "", 0.0, 0.0

    # Extrai distribuicao % e valor
    dist_pct = 0.0
    valor = 0.0
    for cell in row:
        if not cell:
            continue
        cell_str = str(cell).strip()
        # Percentual de distribuicao (ex: "69,24%")
        pct_m = re.match(r'^([\d.,]+)%$', cell_str)
        if pct_m:
            dist_pct = _parse_br_number(pct_m.group(1))
        # Valor investido (ex: "R$ 231.950,74")
        val_m = re.match(r'^R\$\s*([\d.,]+)$', cell_str)
        if val_m:
            v = _parse_br_number(val_m.group(1))
            if v > valor:
                valor = v

    return True, cat_cell, dist_pct, valor


def _find_name_by_value(full_text: str, valor: float) -> str:
    """Tenta encontrar nome do produto no texto completo pelo valor investido."""
    valor_str = f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    # Remove zeros a direita: 10.617,00 -> 10.617
    valor_patterns = [
        valor_str.replace(",00", ""),  # 10.617
        valor_str,                      # 10.617,00
    ]
    lines = full_text.split("\n")
    for i, line in enumerate(lines):
        for vp in valor_patterns:
            if vp in line:
                # Busca nome nas linhas anteriores (ate 5 acima)
                for j in range(max(0, i - 5), i + 1):
                    prev = lines[j].strip()
                    # Busca ticker
                    ticker_m = re.search(r'\(([A-Z]{4}\d{1,2})\)', prev)
                    if ticker_m:
                        return ticker_m.group(1)
                    # Busca nome de fundo (FI/FII + nome)
                    fund_m = re.match(r'^(FI[I]?\s+\w+)', prev)
                    if fund_m:
                        return _clean_name(fund_m.group(1))
    return ""


def _parse_product_table(table: list, categoria: str, total_investido: float,
                         full_text: str = "") -> List[ParsedAssetInst]:
    """Parseia tabela de produtos de uma categoria.

    Cada row: [nome_multiline, rent_mes, rent_mes_ant, rent_ano, ..., valor_investido]
    O nome pode ser None (continuacao da row anterior - produto diferente do mesmo tipo).
    O valor investido esta na ultima coluna (numero puro sem R$).
    """
    ativos = []
    last_nome = ""
    product_index = 0

    for row in table:
        if not row:
            continue

        # Pula linha de "total investido"
        first_cell = str(row[0] or "").strip().lower()
        if "total investido" in first_cell:
            continue

        # Extrai nome (primeira celula, pode ser multiline ou None)
        nome_raw = row[0]
        nome = _clean_name(str(nome_raw)) if nome_raw else ""

        # Se nome vazio, tenta encontrar pelo valor no texto completo
        if not nome:
            # Primeiro, pega o valor para buscar
            temp_valor = 0.0
            for cell in reversed(row):
                if cell is None:
                    continue
                v = _parse_br_number(str(cell).replace("R$", "").strip())
                if v > 0:
                    temp_valor = v
                    break
            if temp_valor > 0 and full_text:
                nome = _find_name_by_value(full_text, temp_valor)
            if not nome:
                product_index += 1
                nome = f"{categoria.split(',')[0].strip()} #{product_index}" if categoria else f"Produto #{product_index}"

        if nome:
            last_nome = nome

        # Extrai valor investido (ultima coluna com numero)
        valor = 0.0
        for cell in reversed(row):
            if cell is None:
                continue
            cell_str = str(cell).strip()
            # Remove R$ se presente
            cell_clean = cell_str.replace("R$", "").strip()
            v = _parse_br_number(cell_clean)
            if v > 0:
                valor = v
                break

        if valor <= 0:
            continue

        # Extrai rentabilidades das celulas intermediarias
        # Formato tipico das celulas: "R$ X,XX\nY,YY%" (valor + percentual)
        rent_mes = 0.0
        rent_ano = 0.0
        rent_12m = 0.0

        # Celulas de rentabilidade (colunas 1 em diante, exceto ultima)
        rent_cells = row[1:-1] if len(row) > 2 else []
        pcts = []
        for cell in rent_cells:
            if cell is None or str(cell).strip() == "-":
                pcts.append(0.0)
                continue
            pcts.append(_extract_pct(str(cell)))

        # Ordem tipica: mes_atual, mes_anterior, ano_atual, ano_anterior, 12m, desde_inicio
        if len(pcts) >= 1:
            rent_mes = pcts[0]
        if len(pcts) >= 3:
            rent_ano = pcts[2]
        if len(pcts) >= 5:
            rent_12m = pcts[4]

        # Ticker e classificacao
        ticker = _extract_ticker(nome)
        tipo = _classify_tipo(categoria, nome)
        display_name = f"{nome} ({ticker})" if ticker and ticker not in nome else nome
        alocacao = (valor / total_investido * 100) if total_investido > 0 else 0.0

        ativos.append(ParsedAssetInst(
            nome=display_name,
            ticker=ticker,
            tipo=tipo,
            subtipo=nome,
            saldo_bruto=valor,
            saldo_liquido=valor,
            impostos=0.0,
            alocacao_pct=round(alocacao, 2),
            rent_mes=rent_mes,
            rent_ano=rent_ano,
            rent_12m=rent_12m,
            indexador=_extract_indexador(nome),
            taxa=_extract_taxa(nome),
            vencimento=_extract_vencimento(nome),
            emissor="",
            instituicao="Itau",
        ))

    return ativos


def parse_itau_pdf(file_path: str) -> InstitutionData:
    """Parseia relatorio Itau Personnalite PDF e retorna InstitutionData."""
    with pdfplumber.open(file_path) as pdf:
        # Texto completo para metadados
        full_text = ""
        for page in pdf.pages:
            full_text += (page.extract_text() or "") + "\n"

        # Extrai total investido
        total_investido = 0.0
        m = re.search(r'total\s+investido\s+R\$\s*([\d.,]+)', full_text, re.IGNORECASE)
        if m:
            total_investido = _parse_br_number(m.group(1))

        # Metadados do cliente
        cliente = ""
        m = re.match(r'^(.+?)\s+ag[eê\x89]ncia\b', full_text, re.IGNORECASE)
        if m:
            cliente = m.group(1).strip()
        if not cliente:
            m = re.match(r'^(.+?)\s+\d{3}\.\d{3}\.\d{3}-\d{2}', full_text)
            if m:
                cliente = m.group(1).strip()

        conta = ""
        m = re.search(r'(\d{3,5})\s+(\d{4,6}-\d)', full_text)
        if m:
            conta = f"{m.group(1)}/{m.group(2)}"

        data_ref = ""
        m = re.search(r'emitido\s+em\s+(\d{2}/\d{2}/\d{4})', full_text, re.IGNORECASE)
        if m:
            data_ref = m.group(1)

        # Extrai ativos via tabelas
        ativos = []
        dist_tipo_cat = {}  # distribuicao por categoria do PDF
        current_categoria = ""

        for page in pdf.pages:
            tables = page.extract_tables()
            for table in tables:
                if not table:
                    continue

                # Verifica se e tabela de categoria
                is_cat, cat_nome, cat_pct, cat_valor = _is_category_table(table)
                if is_cat:
                    current_categoria = cat_nome
                    if cat_pct > 0:
                        dist_tipo_cat[cat_nome] = cat_pct
                    continue

                # Tabela de produtos
                if current_categoria:
                    produtos = _parse_product_table(table, current_categoria, total_investido, full_text)
                    ativos.extend(produtos)

    # Patrimonio
    patrimonio = total_investido
    if not patrimonio and ativos:
        patrimonio = sum(a.saldo_bruto for a in ativos)

    # Distribuicao por tipo (baseada nos ativos parseados)
    dist_tipo = {}
    for a in ativos:
        dist_tipo[a.tipo] = dist_tipo.get(a.tipo, 0.0) + a.alocacao_pct

    # Rentabilidade ponderada da carteira
    rent_mes = 0.0
    rent_ano = 0.0
    rent_12m = 0.0
    if ativos and patrimonio > 0:
        rent_mes = sum(a.rent_mes * a.saldo_bruto for a in ativos) / patrimonio
        rent_ano = sum(a.rent_ano * a.saldo_bruto for a in ativos) / patrimonio
        rent_12m = sum(a.rent_12m * a.saldo_bruto for a in ativos) / patrimonio

    return InstitutionData(
        nome="Itau",
        cliente=cliente,
        conta=conta,
        data_referencia=data_ref,
        patrimonio_bruto=patrimonio,
        patrimonio_liquido=patrimonio,
        impostos_totais=0.0,
        rent_carteira_mes=round(rent_mes, 2),
        rent_carteira_ano=round(rent_ano, 2),
        rent_carteira_12m=round(rent_12m, 2),
        cdi_mes=0.0,
        cdi_ano=0.0,
        perfil_investidor="",
        ativos=ativos,
        distribuicao_tipo=dist_tipo,
    )
