"""Analisador consolidado de carteira."""

from typing import Dict, Any, List
from collections import defaultdict

from agente_investimentos.pdf_reader.models import PortfolioData


def analyze_portfolio(portfolio: PortfolioData, asset_analyses: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Gera análise consolidada da carteira."""

    # Distribuição por tipo
    tipo_dist = defaultdict(lambda: {"count": 0, "saldo": 0.0, "alocacao": 0.0})
    for asset in portfolio.assets:
        tipo_dist[asset.tipo]["count"] += 1
        tipo_dist[asset.tipo]["saldo"] += asset.saldo_bruto
        tipo_dist[asset.tipo]["alocacao"] += asset.alocacao

    # Distribuição por setor - completa com métricas ponderadas e lista de ativos
    total = portfolio.total_bruto or 1
    setor_data = defaultdict(lambda: {
        "count": 0, "saldo": 0.0, "alocacao": 0.0,
        "sum_rent_mes_pond": 0.0, "sum_rent_ano_pond": 0.0,
        "ativos": [],
    })

    for analysis in asset_analyses:
        setor = analysis.get("fundamentals", {}).get("setor", "Outros")
        if not setor or setor == "N/D":
            setor = "Outros"

        saldo = analysis.get("saldo_bruto", 0)
        alocacao = analysis.get("alocacao", 0)
        rent_mes = analysis.get("rent_mes", 0)
        rent_ano = analysis.get("rent_ano", 0)

        sd = setor_data[setor]
        sd["count"] += 1
        sd["saldo"] += saldo
        sd["alocacao"] += alocacao
        sd["sum_rent_mes_pond"] += rent_mes * saldo
        sd["sum_rent_ano_pond"] += rent_ano * saldo
        sd["ativos"].append({
            "ticker": analysis.get("ticker", ""),
            "nome": analysis.get("nome", ""),
            "tipo": analysis.get("tipo", ""),
            "saldo_bruto": saldo,
            "alocacao": alocacao,
            "rent_mes": rent_mes,
            "rent_ano": rent_ano,
        })

    # Calcular métricas ponderadas e montar distribuição final
    distribuição_setor = {}
    for setor, sd in setor_data.items():
        saldo_setor = sd["saldo"] or 1
        distribuição_setor[setor] = {
            "count": sd["count"],
            "saldo": sd["saldo"],
            "alocacao": round(sd["alocacao"], 2),
            "rent_mes_ponderada": round(sd["sum_rent_mes_pond"] / saldo_setor, 2),
            "rent_ano_ponderada": round(sd["sum_rent_ano_pond"] / saldo_setor, 2),
            "ativos": sd["ativos"],
        }

    # Ordenar por alocação (maior primeiro)
    distribuição_setor = dict(
        sorted(distribuição_setor.items(), key=lambda x: x[1]["alocacao"], reverse=True)
    )

    # Métricas ponderadas gerais
    rent_mes_ponderada = sum(a.rent_mes * a.saldo_bruto for a in portfolio.assets) / total
    rent_ano_ponderada = sum(a.rent_ano * a.saldo_bruto for a in portfolio.assets) / total

    # Top performers e piores
    sorted_mes = sorted(portfolio.assets, key=lambda a: a.rent_mes, reverse=True)
    sorted_ano = sorted(portfolio.assets, key=lambda a: a.rent_ano, reverse=True)

    # Concentração (HHI simplificado)
    hhi = sum((a.alocacao / 100) ** 2 for a in portfolio.assets) * 10000
    concentração = "Alta" if hhi > 1500 else "Moderada" if hhi > 1000 else "Baixa"

    return {
        "total_bruto": portfolio.total_bruto,
        "num_ativos": portfolio.num_assets,
        "distribuição_tipo": {k: dict(v) for k, v in tipo_dist.items()},
        "distribuição_setor": distribuição_setor,
        "rent_mes_ponderada": round(rent_mes_ponderada, 2),
        "rent_ano_ponderada": round(rent_ano_ponderada, 2),
        "top_performers_mes": [{"nome": a.nome, "ticker": a.ticker, "rent": a.rent_mes} for a in sorted_mes[:5]],
        "piores_mes": [{"nome": a.nome, "ticker": a.ticker, "rent": a.rent_mes} for a in sorted_mes[-3:]],
        "top_performers_ano": [{"nome": a.nome, "ticker": a.ticker, "rent": a.rent_ano} for a in sorted_ano[:5]],
        "concentração_hhi": round(hhi, 1),
        "nivel_concentração": concentração,
    }
