"""Analisador de Fundos de Investimento (apenas dados do PDF)."""

from typing import Dict, Any

from agente_investimentos.pdf_reader.models import ParsedAsset
from agente_investimentos.data_sources.news_scraper import get_news
from agente_investimentos.data_sources.source_registry import SourceRegistry
from agente_investimentos.analysis.sector_mapper import get_sector


def analyze_fund(asset: ParsedAsset, registry: SourceRegistry) -> Dict[str, Any]:
    """Análise de fundo de investimento usando dados do PDF + notícias."""
    registry.add("PDF", "XP Performance", "", asset.nome, "ok")

    setor = get_sector(asset.ticker, asset.nome, "Fundo")

    # Tenta buscar notícias sobre o fundo
    search_term = asset.nome.split()[0] if asset.nome else ""
    news = []
    if len(search_term) > 3:
        news = get_news(f"{search_term} fundo investimento", registry, max_results=2)

    return {
        "ticker": asset.ticker,
        "nome": asset.nome,
        "tipo": "Fundo",
        "saldo_bruto": asset.saldo_bruto,
        "alocacao": asset.alocacao,
        "rent_mes": asset.rent_mes,
        "rent_ano": asset.rent_ano,
        "cdi_mes": asset.cdi_mes,
        "cdi_ano": asset.cdi_ano,
        "fundamentals": {"setor": setor},
        "dividends": [],
        "news": news,
        "historical_prices": [],
    }
