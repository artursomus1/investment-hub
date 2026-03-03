"""Analisador de ativos de Renda Fixa (apenas dados do PDF)."""

from typing import Dict, Any

from agente_investimentos.pdf_reader.models import ParsedAsset
from agente_investimentos.data_sources.source_registry import SourceRegistry
from agente_investimentos.analysis.sector_mapper import get_sector


def analyze_fixed_income(asset: ParsedAsset, registry: SourceRegistry) -> Dict[str, Any]:
    """Análise de renda fixa usando apenas dados do PDF."""
    registry.add("PDF", "XP Performance", "", asset.nome, "ok")

    setor = get_sector(asset.ticker, asset.nome, "RF")

    return {
        "ticker": asset.ticker,
        "nome": asset.nome,
        "tipo": "RF",
        "saldo_bruto": asset.saldo_bruto,
        "alocacao": asset.alocacao,
        "rent_mes": asset.rent_mes,
        "rent_ano": asset.rent_ano,
        "cdi_mes": asset.cdi_mes,
        "cdi_ano": asset.cdi_ano,
        "fundamentals": {"setor": setor},
        "dividends": [],
        "news": [],
        "historical_prices": [],
    }
