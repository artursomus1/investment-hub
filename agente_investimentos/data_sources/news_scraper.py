"""Scraper de notícias via Google News RSS."""

from typing import List, Dict
from urllib.parse import quote

import feedparser

from agente_investimentos.cache.cache_manager import CacheManager
from agente_investimentos.data_sources.source_registry import SourceRegistry

_cache = CacheManager()

GOOGLE_NEWS_RSS = "https://news.google.com/rss/search"


def get_news(query: str, registry: SourceRegistry, max_results: int = 5) -> List[Dict]:
    """Busca notícias recentes sobre um ativo via Google News RSS."""
    cache_key = query.replace(" ", "_").lower()
    cached = _cache.get("news", cache_key)
    if cached is not None:
        registry.add("RSS", "Google News", GOOGLE_NEWS_RSS, query, "cache")
        return cached

    url = f"{GOOGLE_NEWS_RSS}?q={quote(query)}&hl=pt-BR&gl=BR&ceid=BR:pt-419"

    try:
        feed = feedparser.parse(url)
        articles = []
        for entry in feed.entries[:max_results]:
            articles.append({
                "título": entry.get("title", ""),
                "link": entry.get("link", ""),
                "data": entry.get("published", ""),
                "fonte": entry.get("source", {}).get("title", "") if hasattr(entry, "source") else "",
            })

        _cache.set("news", cache_key, articles)
        registry.add("RSS", "Google News", url, query, "ok")
        return articles

    except Exception as e:
        registry.add("RSS", "Google News", url, query, "erro")
        print(f"  [news] Erro ao buscar notícias de {query}: {e}")
        return []
