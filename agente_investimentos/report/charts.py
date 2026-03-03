"""Geração de gráficos com matplotlib para o relatório."""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pathlib import Path
from typing import Dict, List
import tempfile

from agente_investimentos.report.styles import CHART_PALETTE, MPL_VERDE, MPL_AZUL, MPL_FUNDO


def _setup_style():
    """Configura estilo global dos gráficos."""
    plt.rcParams.update({
        "figure.facecolor": "white",
        "axes.facecolor": "white",
        "font.family": "sans-serif",
        "font.size": 9,
    })


def create_sector_pie(sector_data: Dict[str, Dict], output_path: Path) -> Path:
    """Cria gráfico de pizza com distribuição por setor."""
    _setup_style()

    labels = list(sector_data.keys())
    values = [v["saldo"] for v in sector_data.values()]

    if not values or sum(values) == 0:
        return _create_empty_chart(output_path, "Sem dados de setor")

    # Limita a 8 setores, agrupa resto em "Outros"
    if len(labels) > 8:
        combined = list(zip(labels, values))
        combined.sort(key=lambda x: x[1], reverse=True)
        top = combined[:7]
        rest_val = sum(v for _, v in combined[7:])
        labels = [l for l, _ in top] + ["Outros"]
        values = [v for _, v in top] + [rest_val]

    colors = CHART_PALETTE[:len(labels)]

    fig, ax = plt.subplots(figsize=(6, 4))
    wedges, texts, autotexts = ax.pie(
        values, labels=None, autopct="%1.1f%%",
        colors=colors, startangle=90, pctdistance=0.85,
        textprops={"fontsize": 8}
    )
    ax.legend(labels, loc="center left", bbox_to_anchor=(1, 0.5), fontsize=8)
    ax.set_title("Distribuição por Setor", fontsize=11, fontweight="bold", color=MPL_VERDE)

    plt.tight_layout()
    fig.savefig(output_path, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return output_path


def create_type_bars(type_data: Dict[str, Dict], output_path: Path) -> Path:
    """Cria gráfico de barras com distribuição por tipo de ativo."""
    _setup_style()

    labels = list(type_data.keys())
    values = [v["alocacao"] for v in type_data.values()]

    if not values:
        return _create_empty_chart(output_path, "Sem dados de tipo")

    colors = CHART_PALETTE[:len(labels)]

    fig, ax = plt.subplots(figsize=(6, 3.5))
    bars = ax.barh(labels, values, color=colors, height=0.5)
    ax.set_xlabel("Alocação (%)", fontsize=9)
    ax.set_title("Distribuição por Tipo de Ativo", fontsize=11, fontweight="bold", color=MPL_VERDE)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    for bar, val in zip(bars, values):
        ax.text(bar.get_width() + 0.5, bar.get_y() + bar.get_height() / 2,
                f"{val:.1f}%", va="center", fontsize=8)

    plt.tight_layout()
    fig.savefig(output_path, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return output_path


def create_return_bars(assets: list, output_path: Path, period: str = "mês") -> Path:
    """Cria gráfico de barras com rentabilidade dos ativos."""
    _setup_style()

    if period == "mês":
        data = sorted(assets, key=lambda a: a.rent_mes, reverse=True)[:10]
        values = [a.rent_mes for a in data]
        title = "Top 10 - Rentabilidade Mensal (%)"
    else:
        data = sorted(assets, key=lambda a: a.rent_ano, reverse=True)[:10]
        values = [a.rent_ano for a in data]
        title = "Top 10 - Rentabilidade Anual (%)"

    labels = [a.ticker[:12] for a in data]

    if not values:
        return _create_empty_chart(output_path, "Sem dados")

    colors = [MPL_VERDE if v >= 0 else "#E74C3C" for v in values]

    fig, ax = plt.subplots(figsize=(6, 4))
    bars = ax.barh(labels[::-1], values[::-1], color=colors[::-1], height=0.5)
    ax.set_xlabel("%", fontsize=9)
    ax.set_title(title, fontsize=11, fontweight="bold", color=MPL_VERDE)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.axvline(x=0, color="#999999", linewidth=0.5)

    plt.tight_layout()
    fig.savefig(output_path, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return output_path


def create_price_line_chart(ticker: str, historical_data: list,
                            output_path: Path) -> Path:
    """Cria gráfico de linha com histórico de preços de 1 ano."""
    _setup_style()
    from datetime import datetime

    if not historical_data:
        return _create_empty_chart(output_path, f"Sem dados históricos para {ticker}")

    dates, closes = [], []
    for point in historical_data:
        ts = point.get("date")
        close = point.get("close")
        if ts and close is not None:
            dates.append(datetime.fromtimestamp(ts))
            closes.append(close)

    if len(dates) < 2:
        return _create_empty_chart(output_path, f"Dados insuficientes para {ticker}")

    color = MPL_VERDE if closes[-1] >= closes[0] else "#E74C3C"
    var_pct = ((closes[-1] / closes[0]) - 1) * 100

    fig, ax = plt.subplots(figsize=(7, 2.8))
    ax.plot(dates, closes, color=color, linewidth=1.2, alpha=0.9)
    ax.fill_between(dates, closes, alpha=0.08, color=color)
    ax.annotate(f"R$ {closes[0]:.2f}", xy=(dates[0], closes[0]), fontsize=6, color="#999")
    ax.annotate(f"R$ {closes[-1]:.2f}", xy=(dates[-1], closes[-1]),
                fontsize=7, color=color, fontweight="bold")
    ax.set_title(f"{ticker} - Cotação 12 Meses ({var_pct:+.1f}%)",
                 fontsize=10, fontweight="bold", color=MPL_VERDE)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.tick_params(axis="x", rotation=30, labelsize=6)
    ax.tick_params(axis="y", labelsize=6)
    ax.grid(axis="y", alpha=0.3)

    plt.tight_layout()
    fig.savefig(output_path, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return output_path


def create_dividend_bar_chart(ticker: str, dividends: list,
                              output_path: Path) -> Path:
    """Cria gráfico de barras com histórico de dividendos/rendimentos."""
    _setup_style()
    from datetime import datetime

    if not dividends:
        return _create_empty_chart(output_path, f"Sem dividendos para {ticker}")

    dates, values = [], []
    for div in dividends:
        pay_date = div.get("paymentDate", "")
        rate = div.get("rate", 0)
        if pay_date and rate:
            try:
                dt = datetime.fromisoformat(pay_date.split("T")[0])
                dates.append(dt.strftime("%b/%y"))
                values.append(rate)
            except (ValueError, IndexError):
                continue

    if not values:
        return _create_empty_chart(output_path, f"Sem dividendos para {ticker}")

    dates, values = dates[::-1], values[::-1]  # mais antigo primeiro
    total = sum(values)

    fig, ax = plt.subplots(figsize=(7, 2.5))
    bars = ax.bar(dates, values, color=MPL_AZUL, alpha=0.8, width=0.6)
    for bar, val in zip(bars, values):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.001,
                f"R${val:.2f}", ha="center", va="bottom", fontsize=5)
    ax.set_title(f"{ticker} - Proventos (Total: R$ {total:.2f})",
                 fontsize=10, fontweight="bold", color=MPL_VERDE)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.tick_params(axis="x", rotation=45, labelsize=6)
    ax.tick_params(axis="y", labelsize=6)

    plt.tight_layout()
    fig.savefig(output_path, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return output_path


def _create_empty_chart(output_path: Path, msg: str) -> Path:
    """Cria gráfico placeholder quando não há dados."""
    fig, ax = plt.subplots(figsize=(6, 3))
    ax.text(0.5, 0.5, msg, ha="center", va="center", fontsize=12, color="#999999")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    fig.savefig(output_path, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return output_path
