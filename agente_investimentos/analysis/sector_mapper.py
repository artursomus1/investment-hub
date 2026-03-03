"""Mapeamento de setores para tickers brasileiros (B3 e fundos)."""


# Mapeamento direto ticker -> setor para os tickers mais comuns da B3
SECTOR_MAP = {
    # Bancos e Financeiro
    "ITUB4": "Bancos e Financeiro",
    "ITUB3": "Bancos e Financeiro",
    "BBDC4": "Bancos e Financeiro",
    "BBDC3": "Bancos e Financeiro",
    "BBAS3": "Bancos e Financeiro",
    "SANB11": "Bancos e Financeiro",
    "BPAC11": "Bancos e Financeiro",
    "BPAC3": "Bancos e Financeiro",
    "BPAC5": "Bancos e Financeiro",
    "ABCB4": "Bancos e Financeiro",
    "BRSR6": "Bancos e Financeiro",
    "BMGB4": "Bancos e Financeiro",
    "BPAN4": "Bancos e Financeiro",
    "PINE4": "Bancos e Financeiro",
    "BIDI11": "Bancos e Financeiro",
    "BIDI4": "Bancos e Financeiro",
    "MODL11": "Bancos e Financeiro",
    "INBR32": "Bancos e Financeiro",
    "ROXO34": "Bancos e Financeiro",

    # Seguros e Financeiro Diversificado
    "B3SA3": "Bancos e Financeiro",
    "CIEL3": "Bancos e Financeiro",
    "BBSE3": "Bancos e Financeiro",
    "IRBR3": "Bancos e Financeiro",
    "SULA11": "Bancos e Financeiro",
    "PSSA3": "Bancos e Financeiro",

    # Energia e Utilities
    "ELET3": "Energia e Utilities",
    "ELET6": "Energia e Utilities",
    "EGIE3": "Energia e Utilities",
    "EQTL3": "Energia e Utilities",
    "CMIG4": "Energia e Utilities",
    "CMIG3": "Energia e Utilities",
    "CPFE3": "Energia e Utilities",
    "CPLE6": "Energia e Utilities",
    "CPLE3": "Energia e Utilities",
    "TAEE11": "Energia e Utilities",
    "ENGI11": "Energia e Utilities",
    "AURE3": "Energia e Utilities",
    "AESB3": "Energia e Utilities",
    "NEOE3": "Energia e Utilities",
    "TRPL4": "Energia e Utilities",
    "ENBR3": "Energia e Utilities",
    "CESP6": "Energia e Utilities",
    "SBSP3": "Energia e Utilities",
    "SAPR11": "Energia e Utilities",
    "SAPR4": "Energia e Utilities",
    "CSMG3": "Energia e Utilities",
    "ALUP11": "Energia e Utilities",

    # Petroleo, Gas e Mineracao
    "PETR4": "Petroleo, Gas e Mineracao",
    "PETR3": "Petroleo, Gas e Mineracao",
    "VALE3": "Petroleo, Gas e Mineracao",
    "PRIO3": "Petroleo, Gas e Mineracao",
    "CSAN3": "Petroleo, Gas e Mineracao",
    "RRRP3": "Petroleo, Gas e Mineracao",
    "RECV3": "Petroleo, Gas e Mineracao",
    "BRAP4": "Petroleo, Gas e Mineracao",
    "CSNA3": "Petroleo, Gas e Mineracao",
    "GGBR4": "Petroleo, Gas e Mineracao",
    "GOAU4": "Petroleo, Gas e Mineracao",
    "USIM5": "Petroleo, Gas e Mineracao",

    # Varejo e Consumo
    "MGLU3": "Varejo e Consumo",
    "VIIA3": "Varejo e Consumo",
    "BHIA3": "Varejo e Consumo",
    "LREN3": "Varejo e Consumo",
    "AMER3": "Varejo e Consumo",
    "ARZZ3": "Varejo e Consumo",
    "SOMA3": "Varejo e Consumo",
    "GUAR3": "Varejo e Consumo",
    "CEAB3": "Varejo e Consumo",
    "PETZ3": "Varejo e Consumo",
    "MLAS3": "Varejo e Consumo",
    "AMAR3": "Varejo e Consumo",
    "GRND3": "Varejo e Consumo",
    "VULC3": "Varejo e Consumo",
    "ALPA4": "Varejo e Consumo",
    "NTCO3": "Varejo e Consumo",
    "ABEV3": "Varejo e Consumo",
    "MDIA3": "Varejo e Consumo",
    "JBSS3": "Varejo e Consumo",
    "BRFS3": "Varejo e Consumo",
    "MRFG3": "Varejo e Consumo",
    "BEEF3": "Varejo e Consumo",
    "SMTO3": "Varejo e Consumo",
    "RAIZ4": "Varejo e Consumo",
    "ASAI3": "Varejo e Consumo",
    "CRFB3": "Varejo e Consumo",
    "PCAR3": "Varejo e Consumo",

    # Saude
    "RDOR3": "Saude",
    "HAPV3": "Saude",
    "FLRY3": "Saude",
    "QUAL3": "Saude",
    "HYPE3": "Saude",
    "RADL3": "Saude",
    "PGMN3": "Saude",
    "ONCO3": "Saude",
    "MATD3": "Saude",
    "DASA3": "Saude",

    # Tecnologia e Telecom
    "TOTS3": "Tecnologia e Telecom",
    "LINX3": "Tecnologia e Telecom",
    "LWSA3": "Tecnologia e Telecom",
    "CASH3": "Tecnologia e Telecom",
    "MOSI3": "Tecnologia e Telecom",
    "POSI3": "Tecnologia e Telecom",
    "INTB3": "Tecnologia e Telecom",
    "VIVT3": "Tecnologia e Telecom",
    "TIMS3": "Tecnologia e Telecom",
    "OIBR3": "Tecnologia e Telecom",
    "OIBR4": "Tecnologia e Telecom",

    # Construcao e Imobiliario
    "CYRE3": "Construcao e Imobiliario",
    "MRVE3": "Construcao e Imobiliario",
    "EZTC3": "Construcao e Imobiliario",
    "EVEN3": "Construcao e Imobiliario",
    "DIRR3": "Construcao e Imobiliario",
    "TRIS3": "Construcao e Imobiliario",
    "TEND3": "Construcao e Imobiliario",
    "PLPL3": "Construcao e Imobiliario",
    "LAVV3": "Construcao e Imobiliario",
    "MDNE3": "Construcao e Imobiliario",
    "CURY3": "Construcao e Imobiliario",

    # Transporte e Logistica
    "CCRO3": "Transporte e Logistica",
    "ECOR3": "Transporte e Logistica",
    "RAIL3": "Transporte e Logistica",
    "AZUL4": "Transporte e Logistica",
    "GOLL4": "Transporte e Logistica",
    "EMBR3": "Transporte e Logistica",
    "STBP3": "Transporte e Logistica",
    "HBSA3": "Transporte e Logistica",
    "VAMO3": "Transporte e Logistica",
    "MOVI3": "Transporte e Logistica",
    "RENT3": "Transporte e Logistica",

    # Educacao
    "YDUQ3": "Educacao",
    "COGN3": "Educacao",
    "ANIM3": "Educacao",
    "SEER3": "Educacao",

    # Agronegocio
    "SLCE3": "Agronegocio",
    "AGRO3": "Agronegocio",
    "TTEN3": "Agronegocio",
    "CAML3": "Agronegocio",

    # Shoppings e Propriedades
    "MULT3": "Shoppings e Propriedades",
    "IGTI11": "Shoppings e Propriedades",
    "ALSO3": "Shoppings e Propriedades",
    "BRML3": "Shoppings e Propriedades",

    # Papel e Celulose
    "SUZB3": "Papel e Celulose",
    "KLBN11": "Papel e Celulose",
    "KLBN4": "Papel e Celulose",
    "RANI3": "Papel e Celulose",

    # Siderurgia
    "GGBR3": "Siderurgia",
    "GOAU3": "Siderurgia",

    # Meio Ambiente / Saneamento
    "SAPR3": "Meio Ambiente",

    # === FIIs COMUNS ===
    # Logistica
    "HGLG11": "Imobiliario - Logistica",
    "BTLG11": "Imobiliario - Logistica",
    "XPLG11": "Imobiliario - Logistica",
    "VILG11": "Imobiliario - Logistica",
    "GGRC11": "Imobiliario - Logistica",
    "LVBI11": "Imobiliario - Logistica",

    # Lajes Corporativas
    "HGRE11": "Imobiliario - Lajes",
    "BRCR11": "Imobiliario - Lajes",
    "RBRP11": "Imobiliario - Lajes",
    "JSRE11": "Imobiliario - Lajes",
    "PVBI11": "Imobiliario - Lajes",
    "TEPP11": "Imobiliario - Lajes",

    # Shoppings (FIIs)
    "XPML11": "Imobiliario - Shoppings",
    "VISC11": "Imobiliario - Shoppings",
    "HSML11": "Imobiliario - Shoppings",
    "MALL11": "Imobiliario - Shoppings",

    # Papel / CRI (FIIs de recebíveis)
    "KNCR11": "Imobiliario - Papel",
    "KNIP11": "Imobiliario - Papel",
    "CPTS11": "Imobiliario - Papel",
    "MXRF11": "Imobiliario - Papel",
    "HGCR11": "Imobiliario - Papel",
    "RBRR11": "Imobiliario - Papel",
    "IRDM11": "Imobiliario - Papel",
    "RECR11": "Imobiliario - Papel",
    "VGIR11": "Imobiliario - Papel",
    "VRTA11": "Imobiliario - Papel",
    "PLCR11": "Imobiliario - Papel",
    "RBRY11": "Imobiliario - Papel",
    "DEVA11": "Imobiliario - Papel",
    "NCHB11": "Imobiliario - Papel",
    "CVBI11": "Imobiliario - Papel",

    # Agro (FIIs)
    "KNCA11": "Imobiliario - Agro",
    "RZAG11": "Imobiliario - Agro",
    "FGAA11": "Imobiliario - Agro",

    # Hibrido / FOF
    "KNRI11": "Imobiliario - Hibrido",
    "HFOF11": "Imobiliario - FOF",
    "BCFF11": "Imobiliario - FOF",
    "RBRF11": "Imobiliario - FOF",

    # Residencial
    "MFII11": "Imobiliario - Desenvolvimento",
    "TGAR11": "Imobiliario - Desenvolvimento",
    "URPR11": "Imobiliario - Papel",
}

# Keywords para inferência de setor de FIIs pelo nome
_FII_KEYWORDS = {
    "Imobiliario - Logistica": ["logistic", "logist", "galpao", "galpoes", "industrial", "last mile"],
    "Imobiliario - Lajes": ["laje", "corporativ", "escritorio", "office"],
    "Imobiliario - Shoppings": ["shopping", "shop", "mall", "varejo"],
    "Imobiliario - Papel": ["papel", "cri", "recebi", "credit", "crédito", "high yield", "high grade"],
    "Imobiliario - Agro": ["agro", "agri", "fiagro", "cra"],
    "Imobiliario - Desenvolvimento": ["desenvolvimento", "residenc", "incorpor"],
    "Imobiliario - FOF": ["fof", "fundo de fundo", "fund of fund"],
    "Imobiliario - Hibrido": ["hibrid", "renda urbana", "multiestrateg"],
}

# Keywords para inferência de setor de Fundos
_FUND_KEYWORDS = {
    "Renda Fixa": ["rf", "renda fixa", "firf", "irfm", "ima-", "idka", "cdi", "crédito privado",
                    "credit", "debenture"],
    "Fundos Multimercado": ["multimercado", "macro", "long", "short", "quantitativo",
                            "sistematic", "multiestrateg", "dinamico"],
    "Private Equity": ["private", "equity", "pe ", "fip"],
    "Fundos de Ações": ["fia", "ações", "acao", "ibovespa", "small cap", "dividendo",
                         "valor", "growth"],
    "Previdencia": ["prev", "pgbl", "vgbl"],
    "Fundos Imobiliarios": ["fii", "imobili", "real estate"],
    "Fundos Cambiais": ["cambial", "dolar", "euro", "moeda"],
    "Fundos Internacionais": ["internacional", "global", "offshore", "btg pactual ref di",
                               "exterior", "us ", "sp500", "nasdaq"],
}

# Keywords para classificação de Renda Fixa
_RF_KEYWORDS = {
    "RF - LCA/LCI": ["lca", "lci", "letra de crédito"],
    "RF - CDB": ["cdb"],
    "RF - Tesouro Direto": ["tesouro", "ntn-", "ltn", "lft"],
    "RF - Debenture": ["debenture", "deb "],
    "RF - CRI/CRA": ["cri", "cra", "certificado de recebiveis"],
    "RF - Poupanca": ["poupanca", "poup"],
    "RF - COE": ["coe"],
}


def get_sector(ticker: str, nome: str, tipo: str) -> str:
    """Determina o setor de um ativo.

    Args:
        ticker: Código do ativo (ex: ITUB4, HGLG11)
        nome: Nome completo do ativo
        tipo: Tipo classificado (Acao, FII, RF, Fundo)

    Returns:
        Nome do setor (str)
    """
    # 1. Tenta mapeamento direto
    if ticker in SECTOR_MAP:
        return SECTOR_MAP[ticker]

    nome_lower = nome.lower() if nome else ""

    # 2. FIIs: infere sub-setor por keywords no nome
    if tipo == "FII":
        for setor, keywords in _FII_KEYWORDS.items():
            for kw in keywords:
                if kw in nome_lower:
                    return setor
        return "Imobiliario - Outros"

    # 3. Fundos: infere por keywords
    if tipo == "Fundo":
        for setor, keywords in _FUND_KEYWORDS.items():
            for kw in keywords:
                if kw in nome_lower:
                    return setor
        return "Fundos - Outros"

    # 4. Renda Fixa: classifica por keywords
    if tipo == "RF":
        for setor, keywords in _RF_KEYWORDS.items():
            for kw in keywords:
                if kw in nome_lower:
                    return setor
        return "Renda Fixa"

    # 5. Ações sem mapeamento
    if tipo == "Acao":
        return "Ações - Outros"

    return "Outros"


# Agrupamento de sub-setores em macro-setores
_MACRO_SECTORS = {
    "Imobiliario": [
        "Imobiliario - Logistica", "Imobiliario - Lajes", "Imobiliario - Shoppings",
        "Imobiliario - Papel", "Imobiliario - Agro", "Imobiliario - Desenvolvimento",
        "Imobiliario - FOF", "Imobiliario - Hibrido", "Imobiliario - Outros",
    ],
    "Renda Fixa": [
        "RF - LCA/LCI", "RF - CDB", "RF - Tesouro Direto", "RF - Debenture",
        "RF - CRI/CRA", "RF - Poupanca", "RF - COE", "Renda Fixa",
    ],
    "Fundos": [
        "Renda Fixa", "Fundos Multimercado", "Private Equity", "Fundos de Ações",
        "Previdencia", "Fundos Imobiliarios", "Fundos Cambiais",
        "Fundos Internacionais", "Fundos - Outros",
    ],
}


def get_sector_group(sector: str) -> str:
    """Retorna o macro-setor de um setor específico.

    Args:
        sector: Nome do setor retornado por get_sector()

    Returns:
        Nome do macro-setor
    """
    for macro, setores in _MACRO_SECTORS.items():
        if sector in setores:
            return macro
    return sector
