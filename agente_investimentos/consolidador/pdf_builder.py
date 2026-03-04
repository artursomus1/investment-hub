"""Gerador de PDF consolidado multi-instituicao - Somus Capital.

Estrutura:
1. Capa
2. Uma pagina por instituicao (KPIs + grafico + bullets fortes/fracos + ativos)
3. Consolidado total (visao unificada + graficos)
4. Comparativo entre instituicoes (visual)
5. Pagina tecnica (tabela completa de todos ativos)
"""

import math
import tempfile
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from agente_investimentos.consolidador.models import ConsolidatedPortfolio, InstitutionData
from agente_investimentos.report.base_pdf import SomusPDF, _data_completa, check_space, section_bar
from agente_investimentos.report.styles import (
    VERDE_ESCURO, AZUL, BRANCO, TEXTO, FUNDO_CLARO, CINZA_MEDIO, VERDE_CLARO,
    FONT_TITLE, FONT_BODY,
    SIZE_TITLE, SIZE_SUBTITLE, SIZE_SECTION, SIZE_BODY, SIZE_SMALL, SIZE_TINY,
    MARGIN_LEFT, MARGIN_RIGHT, CONTENT_WIDTH, CHART_PALETTE,
    MPL_VERDE, MPL_AZUL,
)
from agente_investimentos.config import PASTA_SAIDA, LOGO_PATH
from agente_investimentos.utils.formatters import sanitize_text


# ============================================================
# Helpers
# ============================================================

def _fmt_brl(value: float) -> str:
    return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _fmt_pct(value: float) -> str:
    return f"{value:+.2f}%"


def _color_for_value(value: float):
    if value > 0:
        return VERDE_ESCURO
    elif value < 0:
        return (198, 40, 40)
    return TEXTO


VERMELHO = (198, 40, 40)
AMARELO = (243, 156, 18)
LARANJA = (230, 126, 34)


def _setup_mpl():
    plt.rcParams.update({
        "figure.facecolor": "white",
        "axes.facecolor": "white",
        "font.family": "sans-serif",
        "font.size": 9,
    })


def _tmp_path(suffix=".png") -> str:
    return tempfile.mktemp(suffix=suffix)


# ============================================================
# Chart generators
# ============================================================

def _chart_donut_tipos(data: dict, title: str) -> str:
    """Grafico donut de distribuicao por tipo. Retorna path do PNG."""
    _setup_mpl()
    labels = list(data.keys())
    values = [d["saldo_bruto"] if isinstance(d, dict) else d for d in data.values()]
    if not values or sum(values) == 0:
        return ""
    if len(labels) > 8:
        combined = sorted(zip(labels, values), key=lambda x: x[1], reverse=True)
        top = combined[:7]
        rest = sum(v for _, v in combined[7:])
        labels = [l for l, _ in top] + ["Outros"]
        values = [v for _, v in top] + [rest]

    colors = CHART_PALETTE[:len(labels)]
    fig, ax = plt.subplots(figsize=(4.5, 3.2))
    wedges, texts, autotexts = ax.pie(
        values, labels=None, autopct="%1.1f%%",
        colors=colors, startangle=90, pctdistance=0.78,
        wedgeprops=dict(width=0.45, edgecolor="white", linewidth=1.5),
        textprops={"fontsize": 7},
    )
    for t in autotexts:
        t.set_fontsize(6.5)
        t.set_fontweight("bold")
    ax.legend(labels, loc="center left", bbox_to_anchor=(1, 0.5), fontsize=7, frameon=False)
    ax.set_title(title, fontsize=9, fontweight="bold", color=MPL_VERDE, pad=8)
    plt.tight_layout()
    path = _tmp_path()
    fig.savefig(path, dpi=160, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return path


def _chart_bar_comparativo(inst_data: dict) -> str:
    """Barras horizontais comparando patrimonio por instituicao."""
    _setup_mpl()
    labels = list(inst_data.keys())
    values = [d["patrimonio_bruto"] for d in inst_data.values()]
    if not values:
        return ""
    colors = CHART_PALETTE[:len(labels)]
    fig, ax = plt.subplots(figsize=(5, max(2, len(labels) * 0.8)))
    bars = ax.barh(labels[::-1], [v / 1000 for v in values[::-1]],
                   color=colors[::-1], height=0.5, edgecolor="white", linewidth=0.5)
    for bar, val in zip(bars, values[::-1]):
        ax.text(bar.get_width() + 0.5, bar.get_y() + bar.get_height() / 2,
                _fmt_brl(val), va="center", fontsize=7, color="#333")
    ax.set_xlabel("Patrimonio (R$ mil)", fontsize=8)
    ax.set_title("Patrimonio por Instituicao", fontsize=10, fontweight="bold", color=MPL_VERDE)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.tick_params(labelsize=8)
    plt.tight_layout()
    path = _tmp_path()
    fig.savefig(path, dpi=160, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return path


def _chart_rent_comparativo(inst_data: dict) -> str:
    """Barras agrupadas comparando rent mes/ano por instituicao."""
    _setup_mpl()
    labels = list(inst_data.keys())
    rent_mes = [d["rent_mes"] for d in inst_data.values()]
    rent_ano = [d["rent_ano"] for d in inst_data.values()]
    if not labels:
        return ""
    x = range(len(labels))
    w = 0.35
    fig, ax = plt.subplots(figsize=(5, max(2.5, len(labels) * 0.7)))
    bars1 = ax.barh([i - w / 2 for i in x], rent_mes, w, label="Mes", color=MPL_VERDE, alpha=0.85)
    bars2 = ax.barh([i + w / 2 for i in x], rent_ano, w, label="Ano", color=MPL_AZUL, alpha=0.85)
    ax.set_yticks(list(x))
    ax.set_yticklabels(labels, fontsize=8)
    ax.set_xlabel("Rentabilidade (%)", fontsize=8)
    ax.set_title("Rentabilidade por Instituicao", fontsize=10, fontweight="bold", color=MPL_VERDE)
    ax.legend(fontsize=7, loc="lower right")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.axvline(x=0, color="#ccc", linewidth=0.5)
    ax.tick_params(labelsize=7)
    plt.tight_layout()
    path = _tmp_path()
    fig.savefig(path, dpi=160, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return path


def _chart_rent_ativos(ativos: list, title: str, top_n: int = 8) -> str:
    """Barras horizontais de rentabilidade dos ativos (top N)."""
    _setup_mpl()
    if not ativos:
        return ""
    sorted_a = sorted(ativos, key=lambda a: a.rent_ano, reverse=True)
    top = sorted_a[:top_n]
    labels = [a.ticker or a.nome[:18] for a in top]
    values = [a.rent_ano for a in top]
    colors = [MPL_VERDE if v >= 0 else "#E74C3C" for v in values]
    fig, ax = plt.subplots(figsize=(4.5, max(2, len(labels) * 0.5)))
    ax.barh(labels[::-1], values[::-1], color=colors[::-1], height=0.5)
    ax.set_xlabel("Rent. Ano (%)", fontsize=8)
    ax.set_title(title, fontsize=9, fontweight="bold", color=MPL_VERDE)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.axvline(x=0, color="#ccc", linewidth=0.5)
    ax.tick_params(labelsize=7)
    plt.tight_layout()
    path = _tmp_path()
    fig.savefig(path, dpi=160, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return path


# ============================================================
# PDF Builder
# ============================================================

class ConsolidadorPDFBuilder:
    """Gera relatorio PDF consolidado de multiplas instituicoes."""

    def __init__(self, portfolio: ConsolidatedPortfolio):
        self.cp = portfolio
        self._tmp_files = []

    def build(self) -> Path:
        logo = str(LOGO_PATH) if LOGO_PATH.exists() else None
        pdf = SomusPDF(logo_path=logo)
        pdf.set_auto_page_break(auto=True, margin=20)
        pdf.set_margins(MARGIN_LEFT, 15, MARGIN_RIGHT)

        self._add_cover(pdf)

        # 1 pagina por instituicao
        for inst in self.cp.instituicoes:
            self._add_instituicao_page(pdf, inst)

        # Consolidado total
        self._add_consolidado_total(pdf)

        # Comparativo entre instituicoes
        if self.cp.num_instituicoes > 1:
            self._add_comparativo(pdf)

        # Pagina tecnica (todos os ativos)
        self._add_pagina_tecnica(pdf)

        output_path = PASTA_SAIDA / "Relatorio_Consolidado.pdf"
        pdf.output(str(output_path))

        # Cleanup temp files
        for f in self._tmp_files:
            try:
                Path(f).unlink()
            except Exception:
                pass

        return output_path

    def _save_chart(self, path: str):
        if path:
            self._tmp_files.append(path)
        return path

    # ----------------------------------------------------------
    # CAPA
    # ----------------------------------------------------------
    def _add_cover(self, pdf):
        pdf.add_page()
        pdf.skip_footer_on_current_page()

        pdf.set_fill_color(*VERDE_ESCURO)
        pdf.rect(0, 0, 210, 297, "F")

        if LOGO_PATH.exists():
            try:
                pdf.image(str(LOGO_PATH), x=70, y=35, w=70)
            except Exception:
                pass

        pdf.set_y(90)
        pdf.set_font(FONT_TITLE, "B", 30)
        pdf.set_text_color(*BRANCO)
        pdf.cell(CONTENT_WIDTH, 14, "RELATORIO CONSOLIDADO", align="C", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(3)
        pdf.set_font(FONT_BODY, "", 13)
        pdf.cell(CONTENT_WIDTH, 8, "Carteira Multi-Instituicao", align="C", new_x="LMARGIN", new_y="NEXT")

        # Linha decorativa
        pdf.ln(8)
        pdf.set_draw_color(*BRANCO)
        pdf.set_line_width(0.5)
        pdf.line(75, pdf.get_y(), 135, pdf.get_y())

        # KPIs na capa
        pdf.ln(12)
        pdf.set_font(FONT_BODY, "B", 22)
        pdf.cell(CONTENT_WIDTH, 10, _fmt_brl(self.cp.patrimonio_bruto_total), align="C", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font(FONT_BODY, "", 10)
        pdf.set_text_color(200, 220, 210)
        pdf.cell(CONTENT_WIDTH, 6, "Patrimonio Total Consolidado", align="C", new_x="LMARGIN", new_y="NEXT")

        pdf.ln(8)
        pdf.set_font(FONT_BODY, "", 12)
        pdf.set_text_color(*BRANCO)

        # Boxes com info
        box_y = pdf.get_y()
        box_w = CONTENT_WIDTH / 3
        for i, (label, value) in enumerate([
            ("Instituicoes", str(self.cp.num_instituicoes)),
            ("Ativos", str(self.cp.num_ativos_total)),
            ("Rent. Ano", _fmt_pct(self.cp.rent_ano_ponderada())),
        ]):
            x = MARGIN_LEFT + i * box_w
            pdf.set_xy(x, box_y)
            pdf.set_font(FONT_BODY, "B", 16)
            pdf.cell(box_w, 8, value, align="C", new_x="LEFT", new_y="NEXT")
            pdf.set_x(x)
            pdf.set_font(FONT_BODY, "", 8)
            pdf.set_text_color(180, 210, 195)
            pdf.cell(box_w, 5, label, align="C")
            pdf.set_text_color(*BRANCO)

        # Instituicoes listadas
        pdf.set_y(box_y + 25)
        pdf.ln(5)
        pdf.set_font(FONT_BODY, "", 10)
        pdf.set_text_color(200, 220, 210)
        for inst in self.cp.instituicoes:
            pdf.cell(CONTENT_WIDTH, 6,
                     sanitize_text(f"{inst.nome}  -  {_fmt_brl(inst.patrimonio_bruto)}  -  {inst.num_ativos} ativos"),
                     align="C", new_x="LMARGIN", new_y="NEXT")

        # Rodape capa
        pdf.set_y(255)
        pdf.set_font(FONT_BODY, "", 9)
        pdf.set_text_color(150, 180, 170)
        pdf.cell(CONTENT_WIDTH, 6, sanitize_text(f"Gerado em {_data_completa()}"), align="C", new_x="LMARGIN", new_y="NEXT")
        pdf.cell(CONTENT_WIDTH, 6, "Somus Capital - Investment HUB", align="C", new_x="LMARGIN", new_y="NEXT")

    # ----------------------------------------------------------
    # PAGINA POR INSTITUICAO
    # ----------------------------------------------------------
    def _add_instituicao_page(self, pdf, inst: InstitutionData):
        pdf.add_page()
        pdf.set_text_color(*TEXTO)

        # Header com nome da instituicao
        section_bar(pdf, sanitize_text(f"  {inst.nome.upper()}"), color=AZUL)
        pdf.ln(1)

        # ---- KPIs visuais (4 cards) ----
        self._render_kpi_row(pdf, [
            ("Patrimonio Bruto", _fmt_brl(inst.patrimonio_bruto), VERDE_ESCURO),
            ("Num. Ativos", str(inst.num_ativos), AZUL),
            ("Rent. Ano", _fmt_pct(inst.rent_carteira_ano) if inst.rent_carteira_ano else "N/D",
             VERDE_ESCURO if inst.rent_carteira_ano >= 0 else VERMELHO),
            ("Rent. Mes", _fmt_pct(inst.rent_carteira_mes) if inst.rent_carteira_mes else "N/D",
             VERDE_ESCURO if inst.rent_carteira_mes >= 0 else VERMELHO),
        ])
        pdf.ln(2)

        # ---- Info complementar ----
        pdf.set_font(FONT_BODY, "", SIZE_TINY)
        pdf.set_text_color(*CINZA_MEDIO)
        info_parts = []
        if inst.conta:
            info_parts.append(f"Conta: {inst.conta}")
        if inst.data_referencia:
            info_parts.append(f"Ref: {inst.data_referencia}")
        if inst.perfil_investidor:
            info_parts.append(f"Perfil: {inst.perfil_investidor}")
        if inst.rent_carteira_12m:
            info_parts.append(f"Rent. 12m: {_fmt_pct(inst.rent_carteira_12m)}")
        if inst.cdi_ano:
            info_parts.append(f"CDI Ano: {inst.cdi_ano:.1f}%")
        if info_parts:
            pdf.cell(CONTENT_WIDTH, 4, sanitize_text("  |  ".join(info_parts)), new_x="LMARGIN", new_y="NEXT")
        pdf.ln(2)

        # ---- Grafico donut + Bullets lado a lado ----
        dist_tipo = {}
        for a in inst.ativos:
            t = a.tipo
            if t not in dist_tipo:
                dist_tipo[t] = {"saldo_bruto": 0.0, "count": 0}
            dist_tipo[t]["saldo_bruto"] += a.saldo_bruto
            dist_tipo[t]["count"] += 1

        chart_path = self._save_chart(
            _chart_donut_tipos(dist_tipo, f"Composicao - {inst.nome}")
        )

        y_before = pdf.get_y()

        # Coluna esquerda: grafico
        if chart_path:
            try:
                pdf.image(chart_path, x=MARGIN_LEFT, y=y_before, w=90)
            except Exception:
                pass

        # Coluna direita: bullets pontos fortes e fracos
        pdf.set_xy(MARGIN_LEFT + 93, y_before)
        self._render_bullets_fortes_fracos(pdf, inst, x_start=MARGIN_LEFT + 93, width=CONTENT_WIDTH - 93)

        pdf.set_y(max(pdf.get_y(), y_before + 55))
        pdf.ln(3)

        # ---- Tabela de ativos da instituicao ----
        if inst.ativos:
            check_space(pdf, 25)
            self._render_section_label(pdf, "ATIVOS")
            self._render_asset_table(pdf, inst.ativos, show_inst=False)

    def _render_bullets_fortes_fracos(self, pdf, inst: InstitutionData, x_start: float, width: float):
        """Bullet points de pontos fortes e fracos."""
        fortes = []
        fracos = []
        total = inst.patrimonio_bruto or 1

        # Analisa ativos
        ativos_positivos = [a for a in inst.ativos if a.rent_ano > 0]
        ativos_negativos = [a for a in inst.ativos if a.rent_ano < 0]

        # Diversificacao
        tipos_unicos = set(a.tipo for a in inst.ativos)
        if len(tipos_unicos) >= 3:
            fortes.append("Boa diversificacao entre tipos de ativos")
        elif len(tipos_unicos) == 1:
            fracos.append(f"Concentracao total em {list(tipos_unicos)[0]}")

        # Rentabilidade geral
        if inst.rent_carteira_ano > 2:
            fortes.append(f"Rentabilidade anual positiva ({_fmt_pct(inst.rent_carteira_ano)})")
        elif inst.rent_carteira_ano < 0:
            fracos.append(f"Rentabilidade anual negativa ({_fmt_pct(inst.rent_carteira_ano)})")

        # Melhor ativo
        if ativos_positivos:
            best = max(ativos_positivos, key=lambda a: a.rent_ano)
            nome = best.ticker or best.nome[:20]
            fortes.append(f"Destaque: {sanitize_text(nome)} ({_fmt_pct(best.rent_ano)} ano)")

        # Pior ativo
        if ativos_negativos:
            worst = min(ativos_negativos, key=lambda a: a.rent_ano)
            nome = worst.ticker or worst.nome[:20]
            fracos.append(f"Atencao: {sanitize_text(nome)} ({_fmt_pct(worst.rent_ano)} ano)")

        # Concentracao
        if inst.ativos:
            maior = max(inst.ativos, key=lambda a: a.saldo_bruto)
            pct_maior = (maior.saldo_bruto / total * 100)
            if pct_maior > 50:
                fracos.append(f"Concentracao: {pct_maior:.0f}% em um unico ativo")
            elif pct_maior < 30 and len(inst.ativos) >= 3:
                fortes.append("Patrimonio bem distribuido entre ativos")

        # CDI
        if inst.cdi_ano > 100:
            fortes.append(f"Acima de 100% do CDI no ano")
        elif inst.cdi_ano and inst.cdi_ano < 80:
            fracos.append(f"Abaixo de 80% do CDI no ano")

        # Numero de ativos
        if inst.num_ativos >= 5:
            fortes.append(f"{inst.num_ativos} ativos na carteira")

        # Renderiza
        pdf.set_font(FONT_BODY, "B", SIZE_SMALL)
        pdf.set_text_color(*VERDE_ESCURO)
        pdf.set_x(x_start)
        pdf.cell(width, 5, "PONTOS FORTES", new_x="LEFT", new_y="NEXT")

        pdf.set_font(FONT_BODY, "", SIZE_TINY)
        pdf.set_text_color(*TEXTO)
        for bullet in (fortes or ["Nenhum ponto forte identificado"]):
            pdf.set_x(x_start)
            pdf.cell(3, 3.8, "+")
            pdf.multi_cell(width - 3, 3.8, sanitize_text(f" {bullet}"))

        pdf.ln(2)
        pdf.set_font(FONT_BODY, "B", SIZE_SMALL)
        pdf.set_text_color(*VERMELHO)
        pdf.set_x(x_start)
        pdf.cell(width, 5, "PONTOS DE ATENCAO", new_x="LEFT", new_y="NEXT")

        pdf.set_font(FONT_BODY, "", SIZE_TINY)
        pdf.set_text_color(*TEXTO)
        for bullet in (fracos or ["Nenhum ponto critico identificado"]):
            pdf.set_x(x_start)
            pdf.cell(3, 3.8, "-")
            pdf.multi_cell(width - 3, 3.8, sanitize_text(f" {bullet}"))

    # ----------------------------------------------------------
    # CONSOLIDADO TOTAL
    # ----------------------------------------------------------
    def _add_consolidado_total(self, pdf):
        pdf.add_page()
        pdf.set_text_color(*TEXTO)
        section_bar(pdf, "VISAO CONSOLIDADA TOTAL")
        pdf.ln(1)

        # KPIs
        self._render_kpi_row(pdf, [
            ("Patrimonio Total", _fmt_brl(self.cp.patrimonio_bruto_total), VERDE_ESCURO),
            ("Instituicoes", str(self.cp.num_instituicoes), AZUL),
            ("Total Ativos", str(self.cp.num_ativos_total), AZUL),
            ("Rent. Ano", _fmt_pct(self.cp.rent_ano_ponderada()),
             VERDE_ESCURO if self.cp.rent_ano_ponderada() >= 0 else VERMELHO),
        ])
        pdf.ln(3)

        # Graficos lado a lado
        dist_tipo = self.cp.distribuicao_por_tipo()
        chart_tipos = self._save_chart(
            _chart_donut_tipos(dist_tipo, "Composicao por Tipo de Ativo")
        )

        dist_inst = self.cp.distribuicao_por_instituicao()
        chart_inst = self._save_chart(
            _chart_bar_comparativo(dist_inst)
        ) if self.cp.num_instituicoes > 1 else ""

        y_chart = pdf.get_y()
        if chart_tipos:
            try:
                pdf.image(chart_tipos, x=MARGIN_LEFT, y=y_chart, w=88)
            except Exception:
                pass
        if chart_inst:
            try:
                pdf.image(chart_inst, x=MARGIN_LEFT + 92, y=y_chart, w=88)
            except Exception:
                pass

        pdf.set_y(y_chart + 58)

        # Bullets consolidados
        check_space(pdf, 40)
        self._render_section_label(pdf, "DIAGNOSTICO DA CARTEIRA")
        pdf.ln(1)

        bullets = self._generate_consolidated_bullets()
        pdf.set_font(FONT_BODY, "", SIZE_SMALL)
        for emoji_type, text in bullets:
            check_space(pdf, 6)
            if emoji_type == "green":
                pdf.set_text_color(*VERDE_ESCURO)
                prefix = "+"
            elif emoji_type == "red":
                pdf.set_text_color(*VERMELHO)
                prefix = "-"
            else:
                pdf.set_text_color(*AZUL)
                prefix = ">"
            pdf.set_font(FONT_BODY, "B", SIZE_SMALL)
            pdf.cell(4, 5, prefix)
            pdf.set_font(FONT_BODY, "", SIZE_SMALL)
            pdf.set_text_color(*TEXTO)
            pdf.multi_cell(CONTENT_WIDTH - 4, 5, sanitize_text(text))

        # Distribuicao por tipo - barras visuais
        pdf.ln(4)
        check_space(pdf, 30)
        self._render_section_label(pdf, "ALOCACAO POR TIPO")
        pdf.ln(2)
        for tipo, d in dist_tipo.items():
            check_space(pdf, 8)
            pct = d["alocacao"]
            pdf.set_font(FONT_BODY, "B", SIZE_TINY)
            pdf.set_text_color(*TEXTO)
            label = f"{sanitize_text(tipo)}  {pct:.1f}%  ({_fmt_brl(d['saldo_bruto'])})"
            pdf.cell(CONTENT_WIDTH, 4, label, new_x="LMARGIN", new_y="NEXT")
            # Barra
            bar_y = pdf.get_y()
            pdf.set_fill_color(*FUNDO_CLARO)
            pdf.rect(MARGIN_LEFT, bar_y, CONTENT_WIDTH, 3, "F")
            bar_w = max(2, pct / 100 * CONTENT_WIDTH)
            c_idx = list(dist_tipo.keys()).index(tipo)
            hx = CHART_PALETTE[c_idx % len(CHART_PALETTE)]
            pdf.set_fill_color(int(hx[1:3], 16), int(hx[3:5], 16), int(hx[5:7], 16))
            pdf.rect(MARGIN_LEFT, bar_y, bar_w, 3, "F")
            pdf.ln(5)

    def _generate_consolidated_bullets(self):
        """Gera bullets de diagnostico consolidado."""
        bullets = []
        total = self.cp.patrimonio_bruto_total
        dist_inst = self.cp.distribuicao_por_instituicao()
        dist_tipo = self.cp.distribuicao_por_tipo()

        # Patrimonio
        bullets.append(("info", f"Patrimonio consolidado de {_fmt_brl(total)} em {self.cp.num_instituicoes} instituicoes e {self.cp.num_ativos_total} ativos"))

        # Maior instituicao
        if dist_inst:
            maior = max(dist_inst.items(), key=lambda x: x[1]["patrimonio_bruto"])
            pct = maior[1]["alocacao"]
            if pct > 70:
                bullets.append(("red", f"Alta concentracao em {maior[0]} ({pct:.0f}% do patrimonio) - considere diversificar"))
            else:
                bullets.append(("green", f"Patrimonio distribuido entre instituicoes (maior: {maior[0]} com {pct:.0f}%)"))

        # Tipo dominante
        if dist_tipo:
            top_tipo = list(dist_tipo.items())[0]
            pct = top_tipo[1]["alocacao"]
            if pct > 80:
                bullets.append(("red", f"Concentracao em {top_tipo[0]} ({pct:.0f}%) - baixa diversificacao por tipo"))
            elif pct > 60:
                bullets.append(("info", f"Tipo predominante: {top_tipo[0]} com {pct:.0f}% da carteira"))
            else:
                bullets.append(("green", f"Boa diversificacao entre tipos de ativos"))

        # Rentabilidade
        rent_ano = self.cp.rent_ano_ponderada()
        if rent_ano > 2:
            bullets.append(("green", f"Rentabilidade ponderada no ano positiva: {_fmt_pct(rent_ano)}"))
        elif rent_ano < 0:
            bullets.append(("red", f"Rentabilidade ponderada no ano negativa: {_fmt_pct(rent_ano)}"))

        # Risco
        ranking = self.cp.ranking_risco_por_instituicao()
        total_risco = sum(r["saldo_risco"] for r in ranking)
        pct_risco = (total_risco / total * 100) if total else 0
        if pct_risco > 30:
            bullets.append(("red", f"Exposicao a risco elevada: {pct_risco:.0f}% ({_fmt_brl(total_risco)}) em ativos de risco"))
        elif pct_risco > 10:
            bullets.append(("info", f"Exposicao moderada a risco: {pct_risco:.0f}% em ativos de risco"))
        else:
            bullets.append(("green", f"Perfil conservador: apenas {pct_risco:.0f}% em ativos de risco"))

        # Piores performers
        piores = self.cp.piores_rentabilidades()
        if piores and piores[0]["rent_ano"] < -2:
            nome = piores[0]["ticker"] or piores[0]["nome"][:20]
            bullets.append(("red", f"Pior performance: {sanitize_text(nome)} com {_fmt_pct(piores[0]['rent_ano'])} no ano - avaliar troca"))

        # Melhores performers
        melhores = self.cp.melhores_rentabilidades()
        if melhores and melhores[0]["rent_ano"] > 2:
            nome = melhores[0]["ticker"] or melhores[0]["nome"][:20]
            bullets.append(("green", f"Melhor performance: {sanitize_text(nome)} com {_fmt_pct(melhores[0]['rent_ano'])} no ano"))

        return bullets

    # ----------------------------------------------------------
    # COMPARATIVO ENTRE INSTITUICOES
    # ----------------------------------------------------------
    def _add_comparativo(self, pdf):
        pdf.add_page()
        pdf.set_text_color(*TEXTO)
        section_bar(pdf, "COMPARATIVO ENTRE INSTITUICOES")
        pdf.ln(2)

        dist = self.cp.distribuicao_por_instituicao()

        # Tabela comparativa
        cols = [
            ("Instituicao", 32), ("Patrimonio", 32), ("Ativos", 13),
            ("Aloc.", 16), ("Rent. Mes", 22), ("Rent. Ano", 22), ("Rent. 12m", 22),
        ]
        total_w = sum(c[1] for c in cols)
        scale = CONTENT_WIDTH / total_w
        cols = [(n, w * scale) for n, w in cols]

        # Header
        pdf.set_fill_color(*VERDE_ESCURO)
        pdf.set_text_color(*BRANCO)
        pdf.set_font(FONT_BODY, "B", SIZE_TINY)
        for name, w in cols:
            pdf.cell(w, 6, sanitize_text(name), border=0, align="C", fill=True)
        pdf.ln()

        # Rows
        pdf.set_font(FONT_BODY, "", SIZE_TINY)
        for i, (nome, d) in enumerate(dist.items()):
            bg = FUNDO_CLARO if i % 2 == 0 else BRANCO
            pdf.set_fill_color(*bg)
            pdf.set_text_color(*TEXTO)
            pdf.cell(cols[0][1], 5.5, sanitize_text(nome), border=0, fill=True)
            pdf.cell(cols[1][1], 5.5, _fmt_brl(d["patrimonio_bruto"]), border=0, align="R", fill=True)
            pdf.cell(cols[2][1], 5.5, str(d["num_ativos"]), border=0, align="C", fill=True)
            pdf.cell(cols[3][1], 5.5, f"{d['alocacao']:.1f}%", border=0, align="C", fill=True)
            pdf.set_text_color(*_color_for_value(d["rent_mes"]))
            pdf.cell(cols[4][1], 5.5, _fmt_pct(d["rent_mes"]), border=0, align="C", fill=True)
            pdf.set_text_color(*_color_for_value(d["rent_ano"]))
            pdf.cell(cols[5][1], 5.5, _fmt_pct(d["rent_ano"]), border=0, align="C", fill=True)
            r12 = d.get("rent_12m", 0)
            pdf.set_text_color(*_color_for_value(r12))
            pdf.cell(cols[6][1], 5.5, _fmt_pct(r12) if r12 else "-", border=0, align="C", fill=True)
            pdf.ln()

        # Total
        pdf.set_fill_color(*VERDE_ESCURO)
        pdf.set_text_color(*BRANCO)
        pdf.set_font(FONT_BODY, "B", SIZE_TINY)
        pdf.cell(cols[0][1], 6, "TOTAL", border=0, fill=True)
        pdf.cell(cols[1][1], 6, _fmt_brl(self.cp.patrimonio_bruto_total), border=0, align="R", fill=True)
        pdf.cell(cols[2][1], 6, str(self.cp.num_ativos_total), border=0, align="C", fill=True)
        pdf.cell(cols[3][1], 6, "100%", border=0, align="C", fill=True)
        pdf.cell(cols[4][1], 6, _fmt_pct(self.cp.rent_mes_ponderada()), border=0, align="C", fill=True)
        pdf.cell(cols[5][1], 6, _fmt_pct(self.cp.rent_ano_ponderada()), border=0, align="C", fill=True)
        pdf.cell(cols[6][1], 6, "", border=0, align="C", fill=True)
        pdf.ln()
        pdf.set_text_color(*TEXTO)

        # Grafico de rentabilidade comparativa
        pdf.ln(4)
        chart_rent = self._save_chart(_chart_rent_comparativo(dist))
        if chart_rent:
            check_space(pdf, 55)
            try:
                pdf.image(chart_rent, x=MARGIN_LEFT + 15, y=pdf.get_y(), w=CONTENT_WIDTH - 30)
                pdf.set_y(pdf.get_y() + 52)
            except Exception:
                pass

        # Ranking risco
        pdf.ln(3)
        check_space(pdf, 35)
        self._render_section_label(pdf, "EXPOSICAO A RISCO POR INSTITUICAO")
        pdf.ln(2)

        ranking = self.cp.ranking_risco_por_instituicao()
        for r in ranking:
            check_space(pdf, 8)
            pct = r["pct_risco"]
            if pct > 30:
                color = VERMELHO
                indicator = "ALTO"
            elif pct > 10:
                color = AMARELO
                indicator = "MEDIO"
            else:
                color = VERDE_ESCURO
                indicator = "BAIXO"

            pdf.set_font(FONT_BODY, "B", SIZE_SMALL)
            pdf.set_text_color(*TEXTO)
            pdf.cell(40, 5, sanitize_text(r["instituicao"]))

            # Barra de risco
            bar_x = pdf.get_x()
            bar_y = pdf.get_y() + 0.5
            bar_max = 80
            bar_w = max(2, pct / 100 * bar_max)
            pdf.set_fill_color(*FUNDO_CLARO)
            pdf.rect(bar_x, bar_y, bar_max, 4, "F")
            pdf.set_fill_color(*color)
            pdf.rect(bar_x, bar_y, bar_w, 4, "F")

            pdf.set_x(bar_x + bar_max + 3)
            pdf.set_font(FONT_BODY, "B", SIZE_TINY)
            pdf.set_text_color(*color)
            pdf.cell(40, 5, f"{pct:.1f}% - {indicator}")
            pdf.ln(7)

    # ----------------------------------------------------------
    # PAGINA TECNICA - TODOS OS ATIVOS
    # ----------------------------------------------------------
    def _add_pagina_tecnica(self, pdf):
        pdf.add_page()
        pdf.set_text_color(*TEXTO)
        section_bar(pdf, "VISAO TECNICA - TODOS OS ATIVOS CONSOLIDADOS")
        pdf.ln(2)

        pdf.set_font(FONT_BODY, "I", SIZE_TINY)
        pdf.set_text_color(*CINZA_MEDIO)
        pdf.cell(CONTENT_WIDTH, 4, sanitize_text(
            f"Total: {self.cp.num_ativos_total} ativos | Patrimonio: {_fmt_brl(self.cp.patrimonio_bruto_total)} | Ordenado por saldo decrescente"
        ), new_x="LMARGIN", new_y="NEXT")
        pdf.set_text_color(*TEXTO)
        pdf.ln(1)

        all_ativos = sorted(self.cp.todos_ativos, key=lambda a: a.saldo_bruto, reverse=True)
        self._render_asset_table(pdf, all_ativos, show_inst=True)

        # Disclaimer
        pdf.ln(6)
        check_space(pdf, 15)
        pdf.set_font(FONT_BODY, "I", SIZE_TINY)
        pdf.set_text_color(*CINZA_MEDIO)
        pdf.multi_cell(CONTENT_WIDTH, 3.5, sanitize_text(
            "Este relatorio e meramente informativo e nao constitui recomendacao de investimento. "
            "Rentabilidade passada nao garante rentabilidade futura. Consulte seu assessor. "
            "Gerado automaticamente pelo Investment HUB - Somus Capital."
        ))

    # ----------------------------------------------------------
    # Shared renderers
    # ----------------------------------------------------------
    def _render_kpi_row(self, pdf, kpis: list):
        """Renderiza linha de KPI cards. kpis = [(label, value, color), ...]."""
        n = len(kpis)
        card_w = CONTENT_WIDTH / n
        y_start = pdf.get_y()

        for i, (label, value, color) in enumerate(kpis):
            x = MARGIN_LEFT + i * card_w
            # Card background
            pdf.set_fill_color(*color)
            pdf.rect(x + 1, y_start, card_w - 2, 16, "F")
            # Rounded corners effect - small white rects at corners
            # Value
            pdf.set_xy(x + 1, y_start + 1.5)
            pdf.set_font(FONT_BODY, "B", 11 if len(value) < 18 else 9)
            pdf.set_text_color(*BRANCO)
            pdf.cell(card_w - 2, 7, sanitize_text(value), align="C")
            # Label
            pdf.set_xy(x + 1, y_start + 9)
            pdf.set_font(FONT_BODY, "", 6)
            pdf.set_text_color(220, 235, 230)
            pdf.cell(card_w - 2, 5, sanitize_text(label), align="C")

        pdf.set_y(y_start + 18)
        pdf.set_text_color(*TEXTO)

    def _render_section_label(self, pdf, title: str):
        """Mini section label (nao barra inteira)."""
        pdf.set_font(FONT_BODY, "B", SIZE_SMALL)
        pdf.set_text_color(*VERDE_ESCURO)
        # Linha fina
        pdf.set_draw_color(*VERDE_ESCURO)
        pdf.set_line_width(0.3)
        pdf.line(MARGIN_LEFT, pdf.get_y(), MARGIN_LEFT + CONTENT_WIDTH, pdf.get_y())
        pdf.ln(1)
        pdf.cell(CONTENT_WIDTH, 5, sanitize_text(title), new_x="LMARGIN", new_y="NEXT")
        pdf.set_text_color(*TEXTO)
        pdf.ln(1)

    def _render_asset_table(self, pdf, ativos: list, show_inst: bool = False):
        """Tabela de ativos com cores de rentabilidade."""
        if not ativos:
            pdf.set_font(FONT_BODY, "I", SIZE_SMALL)
            pdf.cell(CONTENT_WIDTH, 5, "Nenhum ativo disponivel.", new_x="LMARGIN", new_y="NEXT")
            return

        total_bruto = sum(a.saldo_bruto for a in ativos) or 1

        if show_inst:
            cols = [("Ativo", 38), ("Inst.", 16), ("Tipo", 18), ("Saldo", 27), ("%", 12), ("Mes", 17), ("Ano", 17), ("12m", 17)]
        else:
            cols = [("Ativo", 45), ("Tipo", 20), ("Saldo Bruto", 30), ("% PL", 15), ("Mes", 18), ("Ano", 18), ("12m", 18)]

        total_w = sum(c[1] for c in cols)
        scale = CONTENT_WIDTH / total_w
        cols = [(n, w * scale) for n, w in cols]

        # Header
        pdf.set_fill_color(*VERDE_ESCURO)
        pdf.set_text_color(*BRANCO)
        pdf.set_font(FONT_BODY, "B", SIZE_TINY)
        for name, w in cols:
            pdf.cell(w, 5.5, sanitize_text(name), border=0, align="C", fill=True)
        pdf.ln()

        # Rows
        pdf.set_font(FONT_BODY, "", SIZE_TINY)
        for i, a in enumerate(ativos):
            check_space(pdf, 6)
            bg = FUNDO_CLARO if i % 2 == 0 else BRANCO
            pdf.set_fill_color(*bg)

            nome = a.ticker if a.ticker else a.nome
            max_len = 22 if show_inst else 26
            if len(nome) > max_len:
                nome = nome[:max_len - 2] + ".."
            pct_total = (a.saldo_bruto / total_bruto * 100)

            pdf.set_text_color(*TEXTO)
            col_idx = 0
            pdf.cell(cols[col_idx][1], 5, sanitize_text(nome), border=0, fill=True)
            col_idx += 1

            if show_inst:
                pdf.cell(cols[col_idx][1], 5, sanitize_text(a.instituicao[:10]), border=0, align="C", fill=True)
                col_idx += 1

            pdf.cell(cols[col_idx][1], 5, sanitize_text(a.tipo[:12]), border=0, align="C", fill=True)
            col_idx += 1
            pdf.cell(cols[col_idx][1], 5, _fmt_brl(a.saldo_bruto), border=0, align="R", fill=True)
            col_idx += 1
            pdf.cell(cols[col_idx][1], 5, f"{pct_total:.1f}%", border=0, align="C", fill=True)
            col_idx += 1

            # Rentabilidades com cor
            for val in [a.rent_mes, a.rent_ano, a.rent_12m]:
                pdf.set_text_color(*_color_for_value(val))
                pdf.cell(cols[col_idx][1], 5, _fmt_pct(val) if val else "-", border=0, align="C", fill=True)
                col_idx += 1

            pdf.set_text_color(*TEXTO)
            pdf.ln()
