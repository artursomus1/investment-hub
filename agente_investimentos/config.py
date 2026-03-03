"""Configuração central do agente de investimentos."""

import os
from pathlib import Path
from dotenv import load_dotenv

# Carrega .env do diretório raiz do projeto
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(_PROJECT_ROOT / ".env")

# === Diretórios ===
PASTA_PDFS = _PROJECT_ROOT / "COLETA DE DADOS"
PASTA_SAIDA = _PROJECT_ROOT / "SAIDA DE DADOS"
PASTA_CACHE = Path(__file__).resolve().parent / "cache" / "data"

PASTA_SAIDA.mkdir(parents=True, exist_ok=True)
PASTA_CACHE.mkdir(parents=True, exist_ok=True)


def _get_secret(key: str, default: str = "") -> str:
    """Busca secret em os.environ (.env local) ou st.secrets (Streamlit Cloud)."""
    val = os.getenv(key)
    if val:
        return val
    try:
        import streamlit as st
        return st.secrets.get(key, default)
    except Exception:
        return default


# === API Keys ===
BRAPI_TOKEN = _get_secret("BRAPI_TOKEN")
GEMINI_API_KEY = _get_secret("GEMINI_API_KEY")

# === URLs ===
BRAPI_BASE_URL = "https://brapi.dev/api"
BCB_BASE_URL = "https://api.bcb.gov.br/dados/serie/bcdata.sgs"

# === Cache TTL (segundos) ===
CACHE_TTL_FUNDAMENTALS = 24 * 3600   # 24h
CACHE_TTL_DIVIDENDS = 72 * 3600      # 72h
CACHE_TTL_MACRO = 12 * 3600          # 12h
CACHE_TTL_NEWS_BROAD = 12 * 3600     # 12h - notícias amplas do HUB

# === Cores Somus Capital ===
COR_VERDE_ESCURO = "#004d33"
COR_AZUL = "#1863DC"
COR_TEXTO = "#212121"
COR_FUNDO_CLARO = "#f0f0e0"
COR_BRANCO = "#FFFFFF"

# === Caminhos de assets do report ===
ASSETS_DIR = Path(__file__).resolve().parent / "report" / "assets"
LOGO_PATH = ASSETS_DIR / "logo_somus.png"

# === Gemini ===
GEMINI_MODEL = "gemini-2.5-flash"
GEMINI_MAX_RETRIES = 3
GEMINI_RATE_LIMIT_DELAY = 4.0  # segundos entre chamadas (free tier)
