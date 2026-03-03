"""Classificador de ativos por tipo baseado no ticker/nome."""

import re
from typing import List
from agente_investimentos.pdf_reader.models import ParsedAsset

# Sufixos de FIIs
FII_SUFFIXES = ("11", "11B")

# Palavras-chave de renda fixa
RF_KEYWORDS = (
    "LCA", "LCI", "CDB", "CRI", "CRA", "DEBENTURE", "DEBÊNTURE",
    "TESOURO", "RENDA FIXA", "COMPROMISSADA", "POUPANCA", "POUPANÇA",
    "LC ", "LF ", "DPGE",
)

# Palavras-chave de fundos
FUND_KEYWORDS = (
    "FUNDO", "FI ", "FIC", "FIM", "FIA", "FIRF", "FICFI",
    "MULTIMERCADO", "CRÉDITO", "CRÉDITO", "PREV",
    "SELECTION", "MACRO", "LONG",
)


def classify_asset(asset: ParsedAsset) -> str:
    """Classifica um ativo como: Acao, FII, RF, ou Fundo."""
    ticker = asset.ticker.upper()
    nome = asset.nome.upper()

    # Ação: ticker com 4 letras + 1-2 dígitos (3, 4, 5, 6)
    if re.match(r"^[A-Z]{4}\d{1,2}$", ticker):
        suffix = re.search(r"\d+$", ticker).group()
        if suffix in FII_SUFFIXES:
            return "FII"
        if suffix in ("3", "4", "5", "6", "33", "34"):
            return "Acao"

    # Renda fixa por keywords no nome
    for kw in RF_KEYWORDS:
        if kw in nome:
            return "RF"

    # Fundo por keywords no nome
    for kw in FUND_KEYWORDS:
        if kw in nome:
            return "Fundo"

    # Fallback: se não é ticker padrão, provavelmente é fundo
    if not re.match(r"^[A-Z]{4}\d{1,2}$", ticker):
        return "Fundo"

    return "Acao"  # Default para tickers padrão não classificados


def classify_all(assets: List[ParsedAsset]) -> List[ParsedAsset]:
    """Classifica todos os ativos da carteira."""
    for asset in assets:
        asset.tipo = classify_asset(asset)
    return assets
