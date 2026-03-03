"""Cliente para API do Banco Central do Brasil - CDI e SELIC."""

import requests
from typing import Optional
from datetime import datetime, timedelta

from agente_investimentos.config import BCB_BASE_URL
from agente_investimentos.cache.cache_manager import CacheManager
from agente_investimentos.data_sources.source_registry import SourceRegistry

_cache = CacheManager()

# Códigos das séries do BCB
SERIE_CDI = 12       # CDI diário
SERIE_SELIC = 432    # SELIC meta
SERIE_IPCA = 433     # IPCA mensal


def _fetch_bcb_serie(serie_id: int, últimos: int = 1) -> Optional[float]:
    """Busca último valor de uma série temporal do BCB."""
    url = f"{BCB_BASE_URL}/{serie_id}/dados/últimos/{últimos}"
    params = {"formato": "json"}
    try:
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        if data:
            return float(data[-1]["valor"])
    except (requests.RequestException, ValueError, KeyError, IndexError):
        pass
    return None


def get_macro_data(registry: SourceRegistry) -> dict:
    """Busca CDI, SELIC e IPCA atuais do Banco Central."""
    cached = _cache.get("macro", "bcb_rates")
    if cached is not None:
        registry.add("API", "BCB", BCB_BASE_URL, "", "cache")
        return cached

    result = {}

    cdi = _fetch_bcb_serie(SERIE_CDI)
    if cdi is not None:
        result["cdi_diario"] = cdi
        result["cdi_anual"] = round(((1 + cdi / 100) ** 252 - 1) * 100, 2)
        registry.add("API", "BCB", f"{BCB_BASE_URL}/{SERIE_CDI}/dados/últimos/1", "CDI", "ok")
    else:
        registry.add("API", "BCB", f"{BCB_BASE_URL}/{SERIE_CDI}/dados/últimos/1", "CDI", "erro")

    selic = _fetch_bcb_serie(SERIE_SELIC)
    if selic is not None:
        result["selic_meta"] = selic
        registry.add("API", "BCB", f"{BCB_BASE_URL}/{SERIE_SELIC}/dados/últimos/1", "SELIC", "ok")
    else:
        registry.add("API", "BCB", f"{BCB_BASE_URL}/{SERIE_SELIC}/dados/últimos/1", "SELIC", "erro")

    ipca = _fetch_bcb_serie(SERIE_IPCA)
    if ipca is not None:
        result["ipca_mensal"] = ipca
        registry.add("API", "BCB", f"{BCB_BASE_URL}/{SERIE_IPCA}/dados/últimos/1", "IPCA", "ok")
    else:
        registry.add("API", "BCB", f"{BCB_BASE_URL}/{SERIE_IPCA}/dados/últimos/1", "IPCA", "erro")

    if result:
        _cache.set("macro", "bcb_rates", result)

    return result
