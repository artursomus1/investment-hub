"""Analisador de ações com dados fundamentalistas."""

import statistics
from typing import Dict, Any, Optional

from agente_investimentos.pdf_reader.models import ParsedAsset
from agente_investimentos.data_sources.brapi_client import get_fundamentals, get_dividends, get_historical_prices
from agente_investimentos.data_sources.news_scraper import get_news
from agente_investimentos.data_sources.source_registry import SourceRegistry
from agente_investimentos.analysis.sector_mapper import get_sector


def _calc_potential_metrics(fund_data: dict, hist_data: list) -> dict:
    """Calcula métricas de potencial: distância 52w, volatilidade, sensibilidade."""
    metrics = {}
    preço = fund_data.get("regularMarketPrice")

    # Distância do topo e fundo de 52 semanas
    high_52w = fund_data.get("fiftyTwoWeekHigh")
    low_52w = fund_data.get("fiftyTwoWeekLow")
    if preço and high_52w and high_52w > 0:
        metrics["distancia_52w_high"] = round(((preço / high_52w) - 1) * 100, 2)
    if preço and low_52w and low_52w > 0:
        metrics["distancia_52w_low"] = round(((preço / low_52w) - 1) * 100, 2)
    metrics["fiftyTwoWeekHigh"] = high_52w
    metrics["fiftyTwoWeekLow"] = low_52w

    # Volatilidade anualizada
    if hist_data and len(hist_data) >= 10:
        closes = [h.get("close") for h in hist_data if h.get("close")]
        if len(closes) >= 10:
            returns = [(closes[i] / closes[i - 1] - 1) for i in range(1, len(closes)) if closes[i - 1]]
            if len(returns) > 1:
                vol = statistics.stdev(returns) * (252 ** 0.5) * 100
                metrics["volatilidade"] = round(vol, 1)
                if vol > 40:
                    metrics["score_sensibilidade"] = "Alta"
                elif vol > 25:
                    metrics["score_sensibilidade"] = "Media"
                else:
                    metrics["score_sensibilidade"] = "Baixa"

    return metrics


def analyze_stock(asset: ParsedAsset, registry: SourceRegistry) -> Dict[str, Any]:
    """Análise completa de uma ação com dados fundamentalistas."""
    result = {
        "ticker": asset.ticker,
        "nome": asset.nome,
        "tipo": "Acao",
        "saldo_bruto": asset.saldo_bruto,
        "alocacao": asset.alocacao,
        "rent_mes": asset.rent_mes,
        "rent_ano": asset.rent_ano,
        "cdi_mes": asset.cdi_mes,
        "cdi_ano": asset.cdi_ano,
        "fundamentals": {},
        "dividends": [],
        "news": [],
        "historical_prices": [],
    }

    # Buscar dados fundamentalistas
    fund_data = get_fundamentals(asset.ticker, registry)
    if fund_data:
        setor = get_sector(asset.ticker, asset.nome, "Acao")

        result["fundamentals"] = {
            "preço": fund_data.get("regularMarketPrice"),
            "variação_dia": fund_data.get("regularMarketChangePercent"),
            "market_cap": fund_data.get("marketCap"),
            "setor": setor,
            "industria": fund_data.get("industry", "N/D"),
            "p_l": fund_data.get("priceEarnings"),
            "p_vp": fund_data.get("priceToBook"),
            "roe": fund_data.get("returnOnEquity"),
            "dividend_yield": fund_data.get("dividendYield"),
            "lpa": fund_data.get("earningsPerShare"),
            "vpa": fund_data.get("bookValuePerShare"),
            "ebit_margin": fund_data.get("ebitMargin"),
            "net_margin": fund_data.get("netMargin"),
            "divida_líquida_ebitda": fund_data.get("netDebtToEbitda"),
            "logo": fund_data.get("logourl", ""),
            "nome_longo": fund_data.get("longName", asset.nome),
        }
    else:
        result["fundamentals"] = {
            "setor": get_sector(asset.ticker, asset.nome, "Acao"),
        }

    # Buscar dividendos
    div_data = get_dividends(asset.ticker, registry)
    if div_data:
        result["dividends"] = div_data[:12]

    # Buscar cotações históricas
    hist_data = get_historical_prices(asset.ticker, registry, range_="1y", interval="1d")
    if hist_data:
        result["historical_prices"] = hist_data

    # Métricas de potencial
    if fund_data:
        potential = _calc_potential_metrics(fund_data, hist_data or [])
        result["fundamentals"].update(potential)

    # Buscar notícias
    news = get_news(f"{asset.ticker} ação bolsa", registry, max_results=8)
    result["news"] = news

    return result
