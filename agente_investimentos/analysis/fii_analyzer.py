"""Analisador de Fundos Imobiliários (FIIs)."""

import statistics
from typing import Dict, Any

from agente_investimentos.pdf_reader.models import ParsedAsset
from agente_investimentos.data_sources.brapi_client import get_fundamentals, get_dividends, get_historical_prices
from agente_investimentos.data_sources.news_scraper import get_news
from agente_investimentos.data_sources.source_registry import SourceRegistry
from agente_investimentos.analysis.sector_mapper import get_sector


def _calc_fii_potential(fund_data: dict, hist_data: list) -> dict:
    """Calcula métricas de potencial para FIIs."""
    metrics = {}
    preço = fund_data.get("regularMarketPrice")

    high_52w = fund_data.get("fiftyTwoWeekHigh")
    low_52w = fund_data.get("fiftyTwoWeekLow")
    if preço and high_52w and high_52w > 0:
        metrics["distancia_52w_high"] = round(((preço / high_52w) - 1) * 100, 2)
    if preço and low_52w and low_52w > 0:
        metrics["distancia_52w_low"] = round(((preço / low_52w) - 1) * 100, 2)
    metrics["fiftyTwoWeekHigh"] = high_52w
    metrics["fiftyTwoWeekLow"] = low_52w

    if hist_data and len(hist_data) >= 10:
        closes = [h.get("close") for h in hist_data if h.get("close")]
        if len(closes) >= 10:
            returns = [(closes[i] / closes[i - 1] - 1) for i in range(1, len(closes)) if closes[i - 1]]
            if len(returns) > 1:
                vol = statistics.stdev(returns) * (252 ** 0.5) * 100
                metrics["volatilidade"] = round(vol, 1)
                if vol > 30:
                    metrics["score_sensibilidade"] = "Alta"
                elif vol > 18:
                    metrics["score_sensibilidade"] = "Media"
                else:
                    metrics["score_sensibilidade"] = "Baixa"

    return metrics


def analyze_fii(asset: ParsedAsset, registry: SourceRegistry) -> Dict[str, Any]:
    """Análise de um FII com preço e dividend yield."""
    result = {
        "ticker": asset.ticker,
        "nome": asset.nome,
        "tipo": "FII",
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

    # Dados fundamentalistas
    fund_data = get_fundamentals(asset.ticker, registry)
    if fund_data:
        setor = get_sector(asset.ticker, asset.nome, "FII")

        result["fundamentals"] = {
            "preço": fund_data.get("regularMarketPrice"),
            "variação_dia": fund_data.get("regularMarketChangePercent"),
            "market_cap": fund_data.get("marketCap"),
            "setor": setor,
            "p_vp": fund_data.get("priceToBook"),
            "dividend_yield": fund_data.get("dividendYield"),
            "logo": fund_data.get("logourl", ""),
            "nome_longo": fund_data.get("longName", asset.nome),
        }
    else:
        result["fundamentals"] = {
            "setor": get_sector(asset.ticker, asset.nome, "FII"),
        }

    # Dividendos (rendimentos mensais)
    div_data = get_dividends(asset.ticker, registry)
    if div_data:
        result["dividends"] = div_data[:12]

    # Cotações históricas
    hist_data = get_historical_prices(asset.ticker, registry, range_="1y", interval="1d")
    if hist_data:
        result["historical_prices"] = hist_data

    # Métricas de potencial
    if fund_data:
        potential = _calc_fii_potential(fund_data, hist_data or [])
        result["fundamentals"].update(potential)

    # Notícias
    news = get_news(f"{asset.ticker} fundo imobiliário", registry, max_results=8)
    result["news"] = news

    return result
