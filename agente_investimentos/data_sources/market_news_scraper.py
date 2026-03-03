"""Scraper de notícias amplas por categoria via Google News RSS."""

import time
from dataclasses import dataclass, asdict
from typing import List, Optional
from urllib.parse import quote

import feedparser

from agente_investimentos.cache.cache_manager import CacheManager

_cache = CacheManager()

GOOGLE_NEWS_RSS = "https://news.google.com/rss/search"

# Categorias e suas queries de busca
CATEGORIAS = {
    "Economia": [
        "economia brasileira",
        "PIB Brasil",
        "inflacao IPCA",
        "taxa Selic juros",
        "dolar real cambio",
    ],
    "Politica": [
        "política economica Brasil",
        "governo federal economia",
        "reforma tributaria Brasil",
        "Banco Central Brasil",
    ],
    "Mercado Financeiro": [
        "bolsa de valores B3",
        "Ibovespa hoje",
        "mercado financeiro Brasil",
        "fundos imobiliarios FIIs",
        "renda fixa investimentos",
    ],
    "Esportes": [
        "futebol brasileiro",
        "Brasileirao Serie A",
        "NBA basquete",
    ],
}


@dataclass
class NewsArticle:
    """Artigo de noticia."""
    título: str
    link: str
    data: str
    fonte: str
    categoria: str


def _fetch_rss(query: str, max_results: int = 5) -> List[dict]:
    """Busca artigos via Google News RSS para uma query."""
    url = f"{GOOGLE_NEWS_RSS}?q={quote(query)}&hl=pt-BR&gl=BR&ceid=BR:pt-419"
    try:
        feed = feedparser.parse(url)
        articles = []
        for entry in feed.entries[:max_results]:
            fonte = ""
            if hasattr(entry, "source") and isinstance(entry.source, dict):
                fonte = entry.source.get("title", "")
            elif hasattr(entry, "source") and hasattr(entry.source, "title"):
                fonte = entry.source.title
            articles.append({
                "título": entry.get("title", ""),
                "link": entry.get("link", ""),
                "data": entry.get("published", ""),
                "fonte": fonte,
            })
        return articles
    except Exception as e:
        print(f"  [market_news] Erro ao buscar '{query}': {e}")
        return []


def _deduplicate(articles: List[dict]) -> List[dict]:
    """Remove artigos duplicados por título."""
    seen = set()
    unique = []
    for a in articles:
        key = a["título"].strip().lower()
        if key not in seen:
            seen.add(key)
            unique.append(a)
    return unique


def fetch_broad_news(
    categorias: Optional[List[str]] = None,
    max_per_query: int = 5,
    force_refresh: bool = False,
) -> dict:
    """Busca notícias amplas por categoria.

    Args:
        categorias: Lista de categorias a buscar. None = todas.
        max_per_query: Max artigos por query RSS.
        force_refresh: Ignora cache e busca tudo de novo.

    Returns:
        Dict com chave = categoria, valor = lista de dicts de artigos.
    """
    cats = categorias or list(CATEGORIAS.keys())
    result = {}

    for cat in cats:
        queries = CATEGORIAS.get(cat, [])
        if not queries:
            continue

        cache_key = f"broad_{cat.lower().replace(' ', '_')}"

        if not force_refresh:
            cached = _cache.get("news_broad", cache_key)
            if cached is not None:
                result[cat] = cached
                continue

        all_articles = []
        for q in queries:
            articles = _fetch_rss(q, max_per_query)
            for a in articles:
                a["categoria"] = cat
            all_articles.extend(articles)
            time.sleep(0.5)  # rate limit RSS

        all_articles = _deduplicate(all_articles)
        all_articles.sort(key=lambda x: x.get("data", ""), reverse=True)
        all_articles = all_articles[:20]

        _cache.set("news_broad", cache_key, all_articles)
        result[cat] = all_articles

    return result


def get_all_news_flat(news_by_category: dict) -> List[dict]:
    """Retorna todas as notícias em lista unica, mais recentes primeiro."""
    flat = []
    for cat, articles in news_by_category.items():
        for a in articles:
            a["categoria"] = cat
            flat.append(a)
    flat.sort(key=lambda x: x.get("data", ""), reverse=True)
    return _deduplicate(flat)
