"""Formatadores para valores financeiros brasileiros."""

import re
from datetime import datetime
from typing import Optional

# Mapeamento de caracteres Unicode -> ASCII para FPDF2 (Helvetica/latin-1)
_UNICODE_MAP = {
    '\u201c': '"', '\u201d': '"',   # aspas curvas duplas
    '\u2018': "'", '\u2019': "'",   # aspas curvas simples
    '\u2014': '-', '\u2013': '-',   # travessão em/en dash
    '\u2026': '...', '\u2022': '-', # reticências, bullet
    '\u00b7': '-', '\u2010': '-',   # middle dot, hyphen
    '\u2012': '-', '\u2015': '-',   # figure dash, horizontal bar
    '\u201a': ',', '\u201e': '"',   # single/double low quote
    '\u2032': "'", '\u2033': '"',   # prime, double prime
    '\u2039': '<', '\u203a': '>',   # single angle quotes
    '\u00ab': '<<', '\u00bb': '>>', # double angle quotes
    '\u200b': '', '\u200c': '',     # zero-width space/non-joiner
    '\u200d': '', '\ufeff': '',     # zero-width joiner, BOM
    '\u00a0': ' ',                   # non-breaking space
}


def sanitize_text(text: str) -> str:
    """Remove/substitui caracteres Unicode incompatíveis com latin-1 (FPDF2 Helvetica)."""
    if not text:
        return ""
    for old, new in _UNICODE_MAP.items():
        text = text.replace(old, new)
    # Fallback: qualquer char restante fora de latin-1 vira '?'
    return text.encode('latin-1', 'replace').decode('latin-1')


def parse_br_number(value: str) -> float:
    """Converte número BR (1.234,56) para float. Retorna 0.0 se inválido."""
    if not value or value.strip() == "-":
        return 0.0
    try:
        cleaned = value.strip().replace("%", "").replace("R$", "").strip()
        cleaned = cleaned.replace(".", "").replace(",", ".")
        return float(cleaned)
    except (ValueError, AttributeError):
        return 0.0


def format_brl(value: float) -> str:
    """Formata float como moeda BRL: R$ 1.234,56"""
    if value < 0:
        return f"-R$ {abs(value):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def format_percent(value: float) -> str:
    """Formata float como percentual: 12,34%"""
    return f"{value:,.2f}%".replace(",", "X").replace(".", ",").replace("X", ".")


def format_millions(value: float) -> str:
    """Formata valores grandes em milhões: R$ 1,23M"""
    if abs(value) >= 1_000_000_000:
        return f"R$ {value / 1_000_000_000:,.2f}B".replace(",", "X").replace(".", ",").replace("X", ".")
    if abs(value) >= 1_000_000:
        return f"R$ {value / 1_000_000:,.2f}M".replace(",", "X").replace(".", ",").replace("X", ".")
    if abs(value) >= 1_000:
        return f"R$ {value / 1_000:,.2f}K".replace(",", "X").replace(".", ",").replace("X", ".")
    return format_brl(value)


def parse_percent_str(value: str) -> float:
    """Converte string de percentual BR (-1,23%) para float (-1.23)."""
    return parse_br_number(value)


def parse_news_date(date_str: str) -> Optional[datetime]:
    """Parseia data de RSS (formato RFC 2822, ISO 8601, etc).

    Usada por page_news.py e page_news_impact.py para filtrar noticias por data.
    """
    if not date_str:
        return None
    for fmt in (
        "%a, %d %b %Y %H:%M:%S %Z",
        "%a, %d %b %Y %H:%M:%S %z",
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%d",
    ):
        try:
            return datetime.strptime(date_str.strip(), fmt)
        except ValueError:
            continue
    return None


def extract_client_code(filename: str) -> str:
    """Extrai código do cliente do nome do arquivo XP Performance.
    Ex: 'XPerformance - 3107400 - Ref.10.02 (2).pdf' -> '3107400'
    """
    match = re.search(r"(\d{5,10})", filename)
    return match.group(1) if match else "000000"
