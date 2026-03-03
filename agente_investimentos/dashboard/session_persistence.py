"""Persistencia da sessao de análise em disco.

Salva/carrega o resultado completo da última análise via pickle,
garantindo que Dashboard, Impacto e Migração sempre tenham dados
mesmo após refresh do browser ou reinicio do Streamlit.
"""

import json
import pickle
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Optional

from agente_investimentos.config import PASTA_SAIDA

_SESSION_DIR = PASTA_SAIDA / "last_session"
_SESSION_DIR.mkdir(parents=True, exist_ok=True)

_RESULT_FILE = _SESSION_DIR / "last_result.pkl"
_META_FILE = _SESSION_DIR / "session_meta.json"
_IMPACT_FILE = _SESSION_DIR / "news_impact_text.txt"
_MIGRATION_FILE = _SESSION_DIR / "migration_text.txt"
_DAILY_SUMMARY_FILE = _SESSION_DIR / "daily_summary_text.txt"
_WEEKLY_SUMMARY_FILE = _SESSION_DIR / "weekly_summary_text.txt"
_MONTHLY_SUMMARY_FILE = _SESSION_DIR / "monthly_summary_text.txt"


# === Metadata (JSON) ===

def save_session_meta(result: dict) -> None:
    """Extrai info do portfolio e salva metadata JSON."""
    try:
        portfolio = result.get("portfolio")
        meta = {
            "timestamp": datetime.now().isoformat(),
            "client_code": getattr(portfolio, "client_code", "") if portfolio else "",
            "num_ativos": getattr(portfolio, "num_assets", 0) if portfolio else 0,
            "total_bruto": getattr(portfolio, "total_bruto", 0.0) if portfolio else 0.0,
        }
        _META_FILE.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception as e:
        print(f"[session_persistence] Erro ao salvar meta: {e}")


def load_session_meta() -> Optional[dict]:
    """Carrega metadata da ultima sessao."""
    if not _META_FILE.exists():
        return None
    try:
        return json.loads(_META_FILE.read_text(encoding="utf-8"))
    except Exception:
        return None


def cleanup_old_session(max_days: int = 3) -> bool:
    """Verifica timestamp do meta; se > max_days, deleta todos os arquivos em last_session/.

    Returns True se limpou, False caso contrario.
    """
    meta = load_session_meta()
    if not meta:
        return False
    try:
        ts = datetime.fromisoformat(meta["timestamp"])
        if datetime.now() - ts > timedelta(days=max_days):
            shutil.rmtree(_SESSION_DIR, ignore_errors=True)
            _SESSION_DIR.mkdir(parents=True, exist_ok=True)
            print(f"[session_persistence] Sessao antiga removida (>{max_days} dias)")
            return True
    except Exception as e:
        print(f"[session_persistence] Erro no cleanup: {e}")
    return False


# === Result (pickle) ===

def save_last_result(result: dict) -> None:
    """Salva o resultado completo da análise em disco."""
    try:
        _RESULT_FILE.write_bytes(pickle.dumps(result))
        save_session_meta(result)
    except Exception as e:
        print(f"[session_persistence] Erro ao salvar result: {e}")


def load_last_result() -> Optional[dict]:
    """Carrega o último resultado salvo do disco."""
    if not _RESULT_FILE.exists():
        return None
    try:
        return pickle.loads(_RESULT_FILE.read_bytes())
    except Exception as e:
        print(f"[session_persistence] Erro ao carregar result: {e}")
        return None


# === Textos de IA (texto puro) ===

def save_impact_text(text: str) -> None:
    """Salva texto da análise de impacto."""
    try:
        _IMPACT_FILE.write_text(text, encoding="utf-8")
    except Exception:
        pass


def load_impact_text() -> Optional[str]:
    """Carrega texto da análise de impacto."""
    if not _IMPACT_FILE.exists():
        return None
    try:
        text = _IMPACT_FILE.read_text(encoding="utf-8")
        return text if text.strip() else None
    except Exception:
        return None


def save_migration_text(text: str) -> None:
    """Salva texto das recomendações de migração."""
    try:
        _MIGRATION_FILE.write_text(text, encoding="utf-8")
    except Exception:
        pass


def load_migration_text() -> Optional[str]:
    """Carrega texto das recomendações de migração."""
    if not _MIGRATION_FILE.exists():
        return None
    try:
        text = _MIGRATION_FILE.read_text(encoding="utf-8")
        return text if text.strip() else None
    except Exception:
        return None


def save_daily_summary_text(text: str) -> None:
    """Salva texto do resumo diario."""
    try:
        _DAILY_SUMMARY_FILE.write_text(text, encoding="utf-8")
    except Exception:
        pass


def load_daily_summary_text() -> Optional[str]:
    """Carrega texto do resumo diario."""
    if not _DAILY_SUMMARY_FILE.exists():
        return None
    try:
        text = _DAILY_SUMMARY_FILE.read_text(encoding="utf-8")
        return text if text.strip() else None
    except Exception:
        return None


def save_weekly_summary_text(text: str) -> None:
    """Salva texto do resumo semanal."""
    try:
        _WEEKLY_SUMMARY_FILE.write_text(text, encoding="utf-8")
    except Exception:
        pass


def load_weekly_summary_text() -> Optional[str]:
    """Carrega texto do resumo semanal."""
    if not _WEEKLY_SUMMARY_FILE.exists():
        return None
    try:
        text = _WEEKLY_SUMMARY_FILE.read_text(encoding="utf-8")
        return text if text.strip() else None
    except Exception:
        return None


def save_monthly_summary_text(text: str) -> None:
    """Salva texto do resumo mensal."""
    try:
        _MONTHLY_SUMMARY_FILE.write_text(text, encoding="utf-8")
    except Exception:
        pass


def load_monthly_summary_text() -> Optional[str]:
    """Carrega texto do resumo mensal."""
    if not _MONTHLY_SUMMARY_FILE.exists():
        return None
    try:
        text = _MONTHLY_SUMMARY_FILE.read_text(encoding="utf-8")
        return text if text.strip() else None
    except Exception:
        return None


def ensure_session_state() -> None:
    """Garante que session_state tem os dados da última análise.

    Chame no inicio de qualquer página que dependa de last_result.
    Carrega do disco se necessário.
    """
    import streamlit as st

    # last_result
    if not st.session_state.get("last_result"):
        saved = load_last_result()
        if saved:
            st.session_state["last_result"] = saved

    # news_impact_text
    if not st.session_state.get("news_impact_text"):
        saved = load_impact_text()
        if saved:
            st.session_state["news_impact_text"] = saved

    # migration_text
    if not st.session_state.get("migration_text"):
        saved = load_migration_text()
        if saved:
            st.session_state["migration_text"] = saved

    # daily_summary_text
    if not st.session_state.get("daily_summary_text"):
        saved = load_daily_summary_text()
        if saved:
            st.session_state["daily_summary_text"] = saved

    # weekly_summary_text
    if not st.session_state.get("weekly_summary_text"):
        saved = load_weekly_summary_text()
        if saved:
            st.session_state["weekly_summary_text"] = saved

    # monthly_summary_text
    if not st.session_state.get("monthly_summary_text"):
        saved = load_monthly_summary_text()
        if saved:
            st.session_state["monthly_summary_text"] = saved
