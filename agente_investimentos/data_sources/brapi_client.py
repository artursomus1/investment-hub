"""Cliente para API brapi.dev - dados fundamentalistas de ações e FIIs."""

import requests
from typing import Dict, Any, Optional, List

from agente_investimentos.config import BRAPI_TOKEN, BRAPI_BASE_URL
from agente_investimentos.cache.cache_manager import CacheManager
from agente_investimentos.data_sources.source_registry import SourceRegistry
from agente_investimentos.utils.exceptions import APIError

_cache = CacheManager()


def get_fundamentals(ticker: str, registry: SourceRegistry) -> Optional[Dict[str, Any]]:
    """Busca dados fundamentalistas de um ticker na brapi.dev."""
    # Tenta cache
    cached = _cache.get("fundamentals", ticker)
    if cached is not None:
        registry.add("API", "brapi.dev", f"{BRAPI_BASE_URL}/quote/{ticker}", ticker, "cache")
        return cached

    url = f"{BRAPI_BASE_URL}/quote/{ticker}"
    params = {"token": BRAPI_TOKEN, "fundamental": "true"}

    try:
        resp = requests.get(url, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()

        results = data.get("results", [])
        if not results:
            registry.add("API", "brapi.dev", url, ticker, "erro")
            return None

        result = results[0]
        _cache.set("fundamentals", ticker, result)
        registry.add("API", "brapi.dev", url, ticker, "ok")
        return result

    except requests.RequestException as e:
        registry.add("API", "brapi.dev", url, ticker, "erro")
        print(f"  [brapi] Erro ao buscar {ticker}: {e}")
        return None


def get_dividends(ticker: str, registry: SourceRegistry) -> Optional[List[Dict]]:
    """Busca histórico de dividendos de um ticker."""
    cached = _cache.get("dividends", ticker)
    if cached is not None:
        registry.add("API", "brapi.dev", f"{BRAPI_BASE_URL}/quote/{ticker}", ticker, "cache")
        return cached

    url = f"{BRAPI_BASE_URL}/quote/{ticker}"
    params = {"token": BRAPI_TOKEN, "dividends": "true", "range": "1y"}

    try:
        resp = requests.get(url, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()

        results = data.get("results", [])
        if not results:
            registry.add("API", "brapi.dev", url, ticker, "erro")
            return None

        dividends = results[0].get("dividendsData", {}).get("cashDividends", [])
        _cache.set("dividends", ticker, dividends)
        registry.add("API", "brapi.dev", url, ticker, "ok")
        return dividends

    except requests.RequestException as e:
        registry.add("API", "brapi.dev", url, ticker, "erro")
        print(f"  [brapi] Erro dividendos {ticker}: {e}")
        return None


def get_historical_prices(ticker: str, registry: SourceRegistry,
                          range_: str = "1y", interval: str = "1d") -> Optional[List[Dict]]:
    """Busca cotações historicas de um ticker na brapi.dev."""
    cache_key = f"hist_{ticker}_{range_}_{interval}"
    cached = _cache.get("fundamentals", cache_key)
    if cached is not None:
        registry.add("API", "brapi.dev", f"{BRAPI_BASE_URL}/quote/{ticker}", ticker, "cache")
        return cached

    url = f"{BRAPI_BASE_URL}/quote/{ticker}"
    params = {"token": BRAPI_TOKEN, "range": range_, "interval": interval}

    try:
        resp = requests.get(url, params=params, timeout=20)
        resp.raise_for_status()
        data = resp.json()

        results = data.get("results", [])
        if not results:
            registry.add("API", "brapi.dev", url, ticker, "erro")
            return None

        historical = results[0].get("historicalDataPrice", [])
        if not historical:
            registry.add("API", "brapi.dev", url, ticker, "erro")
            return None

        _cache.set("fundamentals", cache_key, historical)
        registry.add("API", "brapi.dev", url, ticker, "ok")
        return historical

    except requests.RequestException as e:
        registry.add("API", "brapi.dev", url, ticker, "erro")
        print(f"  [brapi] Erro histórico {ticker}: {e}")
        return None
