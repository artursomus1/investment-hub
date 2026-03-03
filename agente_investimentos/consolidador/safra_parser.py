"""Parser para relatorios do Banco Safra (PDF)."""

import re
from typing import Optional

import pdfplumber

from agente_investimentos.consolidador.models import ParsedAssetInst, InstitutionData


def _parse_br_number(text: str) -> float:
    """Converte numero BR '1.234,56' para float."""
    if not text or text.strip() in ("-", ""):
        return 0.0
    text = text.strip().replace(".", "").replace(",", ".")
    try:
        return float(text)
    except ValueError:
        return 0.0


def _find_page_by_title(pdf, title: str) -> Optional[int]:
    """Encontra indice da pagina que contem determinado titulo."""
    for i, page in enumerate(pdf.pages):
        text = page.extract_text() or ""
        if title in text:
            return i
    return None


def _parse_posicao_investimentos(text: str, instituicao: str) -> list:
    """Extrai ativos da pagina 'Posicao de Investimentos' do Safra.

    Formato tipico:
    RENDA FIXA 7.813.782,17 41.072,11 7.772.710,06 94,92 0,91 2,41 16,90
    CRA Emissao Terceiros CDI 148.238,21 - 148.238,21 1,80 -4,78 -1,56 1,01
    """
    ativos = []
    lines = text.split("\n")

    # Categorias de grupo (headers)
    _CATEGORIAS = {
        "RENDA FIXA": "Renda Fixa",
        "MULTIMERCADO": "Multimercado",
        "OP. ESTRUTURADAS": "Op. Estruturadas",
        "CURTO PRAZO": "Curto Prazo",
        "RENDA VARIAVEL": "Renda Variavel",
        "PREVIDENCIA": "Previdencia",
    }

    current_tipo = ""

    # Regex para linhas de ativo com numeros
    # Nome ... saldo_bruto impostos sld_liquido %PL rent_mes rent_ano rent_12m
    pattern = re.compile(
        r'^(.+?)\s+'
        r'([\d.,]+)\s+'       # saldo bruto
        r'([\d.,-]+)\s+'      # impostos
        r'([\d.,]+)\s+'       # saldo liquido
        r'([\d.,]+)\s+'       # % PL
        r'(-?[\d.,]+)\s+'     # rent mes
        r'(-?[\d.,]+)\s+'     # rent ano
        r'(-?[\d.,]+)'        # rent 12m
    )

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue

        # Ignora headers e notas
        if stripped.startswith(("1.", "Patrimonio", "Resumo", "Sld ", "Relatorio")):
            continue

        # Detecta categoria
        for cat_key, cat_val in _CATEGORIAS.items():
            if stripped.startswith(cat_key):
                current_tipo = cat_val
                break

        m = pattern.match(stripped)
        if not m:
            continue

        nome = m.group(1).strip()
        saldo_bruto = _parse_br_number(m.group(2))
        impostos = _parse_br_number(m.group(3))
        saldo_liq = _parse_br_number(m.group(4))
        aloc_pct = _parse_br_number(m.group(5))
        rent_mes = _parse_br_number(m.group(6))
        rent_ano = _parse_br_number(m.group(7))
        rent_12m = _parse_br_number(m.group(8))

        # Ignora linhas de total (que sao categorias de grupo)
        if nome.upper() in _CATEGORIAS:
            continue

        # Determina subtipo e indexador
        subtipo = nome
        indexador = ""
        taxa = ""
        if "CDI" in nome.upper():
            indexador = "CDI"
        elif "IPCA" in nome.upper():
            indexador = "IPCA"
        elif "PRE" in nome.upper():
            indexador = "PRE"

        # Determina tipo se nao herdou da categoria
        tipo = current_tipo
        if not tipo:
            if any(k in nome.upper() for k in ("CDB", "LCA", "LCI", "CRA", "CRI", "DEBENTURE")):
                tipo = "Renda Fixa"
            elif "MULTIMERCADO" in nome.upper() or "INTELIGENCIA" in nome.upper():
                tipo = "Multimercado"
            else:
                tipo = "Renda Fixa"

        ativos.append(ParsedAssetInst(
            nome=nome,
            ticker="",
            tipo=tipo,
            subtipo=subtipo,
            saldo_bruto=saldo_bruto,
            saldo_liquido=saldo_liq,
            impostos=impostos,
            alocacao_pct=aloc_pct,
            rent_mes=rent_mes,
            rent_ano=rent_ano,
            rent_12m=rent_12m,
            indexador=indexador,
            taxa=taxa,
            vencimento="",
            emissor="",
            instituicao=instituicao,
        ))

    return ativos


def _parse_carteira_resumo(text: str) -> dict:
    """Extrai dados resumo da carteira (pagina 2 do Safra).

    Linha tipica:
    Carteira 8.232.065,65 1.598.614,55 48.162,71 8.183.902,94 0,91 91,14 2,45 112,55 16,89 116,48
    """
    result = {
        "patrimonio_bruto": 0.0,
        "patrimonio_liquido": 0.0,
        "impostos": 0.0,
        "rent_mes": 0.0,
        "cdi_mes": 0.0,
        "rent_ano": 0.0,
        "cdi_ano": 0.0,
        "rent_12m": 0.0,
        "perfil_investidor": "",
    }

    for line in text.split("\n"):
        stripped = line.strip()
        if stripped.startswith("Carteira"):
            nums = re.findall(r'-?[\d.,]+', stripped[len("Carteira"):])
            if len(nums) >= 10:
                result["patrimonio_bruto"] = _parse_br_number(nums[0])
                # nums[1] = saldo USD
                result["impostos"] = _parse_br_number(nums[2])
                result["patrimonio_liquido"] = _parse_br_number(nums[3])
                result["rent_mes"] = _parse_br_number(nums[4])
                result["cdi_mes"] = _parse_br_number(nums[5])
                result["rent_ano"] = _parse_br_number(nums[6])
                result["cdi_ano"] = _parse_br_number(nums[7])
                result["rent_12m"] = _parse_br_number(nums[8])
        elif "Perfil do Cliente" in stripped or "Moderado" in stripped or "Conservador" in stripped or "Arrojado" in stripped:
            for perfil in ["Conservador", "Moderado", "Arrojado", "Agressivo"]:
                if perfil in stripped:
                    result["perfil_investidor"] = perfil
                    break

    return result


def _extract_conta(text: str) -> str:
    """Extrai numero da conta."""
    m = re.search(r'Conta[:\s]*(\S+)', text)
    return m.group(1) if m else ""


def _extract_data_ref(text: str) -> str:
    """Extrai data de referencia."""
    m = re.search(r'Data da posi[çc][ãa]o:\s*(\d{2}/\d{2}/\d{4})', text)
    return m.group(1) if m else ""


def _extract_nome_banker(text: str) -> str:
    """Extrai nome do cliente ou banker."""
    m = re.search(r'Nr\.\s*de\s*Conta\s*Corrente:\s*(\S+)', text)
    return m.group(1) if m else ""


def parse_safra_pdf(file_path: str) -> InstitutionData:
    """Parseia relatorio Safra PDF e retorna InstitutionData."""
    with pdfplumber.open(file_path) as pdf:
        # Pagina 1: dados gerais
        page1_text = pdf.pages[0].extract_text() or "" if len(pdf.pages) > 0 else ""

        # Pagina 2: resumo carteira + perfil
        page2_text = pdf.pages[1].extract_text() or "" if len(pdf.pages) > 1 else ""

        # Encontra pagina de "Posicao de Investimentos"
        posicao_text = ""
        for page in pdf.pages:
            text = page.extract_text() or ""
            if "Posição de Investimentos" in text or "Posicao de Investimentos" in text:
                posicao_text = text
                break

        # Dados resumo
        resumo = _parse_carteira_resumo(page2_text)

        # Perfil do investidor (busca em page2)
        perfil = resumo["perfil_investidor"]
        if not perfil:
            for page in pdf.pages[:3]:
                text = page.extract_text() or ""
                for p in ["Conservador", "Moderado", "Arrojado", "Agressivo"]:
                    if p in text:
                        perfil = p
                        break
                if perfil:
                    break

        # Dados da conta
        conta = _extract_conta(page2_text) or _extract_conta(page1_text)
        data_ref = _extract_data_ref(page2_text) or _extract_data_ref(page1_text)

        # Ativos
        ativos = _parse_posicao_investimentos(posicao_text, "Safra") if posicao_text else []

        # Distribuicao por tipo
        dist_tipo = {}
        for line in page2_text.split("\n"):
            # "Renda fixa | 94.92 %"
            m = re.match(r'(.+?)\s*\|\s*([\d.,]+)\s*%', line)
            if m:
                tipo_nome = m.group(1).strip()
                pct = _parse_br_number(m.group(2))
                dist_tipo[tipo_nome] = pct

        return InstitutionData(
            nome="Safra",
            cliente=conta,
            conta=conta,
            data_referencia=data_ref,
            patrimonio_bruto=resumo["patrimonio_bruto"],
            patrimonio_liquido=resumo["patrimonio_liquido"],
            impostos_totais=resumo["impostos"],
            rent_carteira_mes=resumo["rent_mes"],
            rent_carteira_ano=resumo["rent_ano"],
            rent_carteira_12m=resumo["rent_12m"],
            cdi_mes=resumo["cdi_mes"],
            cdi_ano=resumo["cdi_ano"],
            perfil_investidor=perfil,
            ativos=ativos,
            distribuicao_tipo=dist_tipo,
        )
