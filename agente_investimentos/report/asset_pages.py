"""Páginas individuais de análise por ativo."""

from fpdf import FPDF
from typing import Dict, Any

from agente_investimentos.report.styles import (
    VERDE_ESCURO, AZUL, BRANCO, TEXTO, FUNDO_CLARO, CINZA_MEDIO, VERDE_CLARO,
    FONT_TITLE, FONT_BODY, SIZE_SECTION, SIZE_BODY, SIZE_SMALL, SIZE_TINY,
    MARGIN_LEFT, CONTENT_WIDTH,
)
from agente_investimentos.utils.formatters import format_brl, format_percent, sanitize_text


def _asset_header(pdf: FPDF, analysis: Dict):
    """Cabeçalho do ativo com ticker e tipo."""
    tipo = analysis.get("tipo", "")
    ticker = analysis.get("ticker", "")
    nome = analysis.get("nome", "")

    # Badge de tipo
    tipo_colors = {
        "Acao": VERDE_ESCURO,
        "FII": AZUL,
        "RF": CINZA_MEDIO,
        "Fundo": VERDE_CLARO,
    }
    color = tipo_colors.get(tipo, CINZA_MEDIO)

    pdf.set_fill_color(*color)
    pdf.set_text_color(*BRANCO)
    pdf.set_font(FONT_BODY, "B", SIZE_SMALL)
    pdf.cell(20, 7, f" {tipo} ", fill=True)

    pdf.set_text_color(*TEXTO)
    pdf.set_font(FONT_TITLE, "B", SIZE_SECTION)
    pdf.cell(5, 7, "")  # spacer
    pdf.cell(0, 7, f"{ticker}", new_x="LMARGIN", new_y="NEXT")

    pdf.set_font(FONT_BODY, "", SIZE_BODY)
    pdf.set_text_color(*CINZA_MEDIO)
    nome_display = sanitize_text(nome[:70] if len(nome) > 70 else nome)
    pdf.cell(CONTENT_WIDTH, 6, nome_display, new_x="LMARGIN", new_y="NEXT")
    pdf.ln(3)


def _metrics_grid(pdf: FPDF, analysis: Dict):
    """Grid de métricas do ativo."""
    pdf.set_text_color(*TEXTO)

    # Métricas do PDF
    metrics_pdf = [
        ("Saldo Bruto", format_brl(analysis["saldo_bruto"])),
        ("Alocação", format_percent(analysis["alocacao"])),
        ("Rent. Mês", format_percent(analysis["rent_mes"])),
        ("%CDI Mês", format_percent(analysis["cdi_mes"])),
        ("Rent. Ano", format_percent(analysis["rent_ano"])),
        ("%CDI Ano", format_percent(analysis["cdi_ano"])),
    ]

    # Métricas fundamentalistas (se disponíveis)
    fund = analysis.get("fundamentals", {})
    if fund:
        if fund.get("preço") is not None:
            metrics_pdf.append(("Preço", f"R$ {fund['preço']:.2f}"))
        if fund.get("p_l") is not None:
            metrics_pdf.append(("P/L", f"{fund['p_l']:.2f}"))
        if fund.get("p_vp") is not None:
            metrics_pdf.append(("P/VP", f"{fund['p_vp']:.2f}"))
        if fund.get("dividend_yield") is not None:
            metrics_pdf.append(("DY", f"{fund['dividend_yield']:.2f}%"))
        if fund.get("roe") is not None:
            metrics_pdf.append(("ROE", f"{fund['roe']:.2f}%"))

    # Renderiza em grid 3 colunas
    col_w = CONTENT_WIDTH / 3
    y_start = pdf.get_y()

    for i, (label, value) in enumerate(metrics_pdf):
        col = i % 3
        row = i // 3
        x = MARGIN_LEFT + col * col_w
        y = y_start + row * 14

        if y > 270:
            pdf.add_page()
            y_start = pdf.get_y()
            y = y_start

        pdf.set_xy(x, y)
        pdf.set_font(FONT_BODY, "", SIZE_TINY)
        pdf.set_text_color(*CINZA_MEDIO)
        pdf.cell(col_w - 2, 5, label)

        pdf.set_xy(x, y + 5)
        pdf.set_font(FONT_BODY, "B", SIZE_BODY)
        pdf.set_text_color(*TEXTO)
        pdf.cell(col_w - 2, 6, value)

    # Move para abaixo do grid
    total_rows = (len(metrics_pdf) + 2) // 3
    pdf.set_xy(MARGIN_LEFT, y_start + total_rows * 14 + 4)


def _fundamentals_section(pdf: FPDF, analysis: Dict):
    """Seção de dados fundamentalistas (ações e FIIs)."""
    fund = analysis.get("fundamentals", {})
    if not fund:
        return

    setor = fund.get("setor", "N/D")
    industria = fund.get("industria", "")

    if setor and setor != "N/D":
        pdf.set_font(FONT_BODY, "", SIZE_SMALL)
        pdf.set_text_color(*CINZA_MEDIO)
        label = f"Setor: {setor}"
        if industria and industria != "N/D":
            label += f" | {industria}"
        pdf.cell(CONTENT_WIDTH, 5, label, new_x="LMARGIN", new_y="NEXT")
        pdf.ln(2)

    # Indicadores extras para ações
    tipo = analysis.get("tipo", "")
    if tipo == "Acao":
        extras = []
        if fund.get("ebit_margin") is not None:
            extras.append(f"Margem EBIT: {fund['ebit_margin']:.1f}%")
        if fund.get("net_margin") is not None:
            extras.append(f"Margem Líq.: {fund['net_margin']:.1f}%")
        if fund.get("divida_líquida_ebitda") is not None:
            extras.append(f"Dív.Líq./EBITDA: {fund['divida_líquida_ebitda']:.2f}")

        if extras:
            pdf.set_font(FONT_BODY, "", SIZE_TINY)
            pdf.set_text_color(*TEXTO)
            pdf.cell(CONTENT_WIDTH, 5, " | ".join(extras), new_x="LMARGIN", new_y="NEXT")
            pdf.ln(2)


def _ai_analysis_section(pdf: FPDF, ai_text: str):
    """Seção com análise gerada pela IA."""
    if not ai_text or ai_text == "Análise IA indisponível para este ativo.":
        return

    ai_text = sanitize_text(ai_text)

    pdf.set_fill_color(*FUNDO_CLARO)
    pdf.set_font(FONT_BODY, "B", SIZE_SMALL)
    pdf.set_text_color(*VERDE_ESCURO)
    pdf.cell(CONTENT_WIDTH, 7, "  Análise IA (Gemini)", fill=True, new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)

    pdf.set_text_color(*TEXTO)
    pdf.set_font(FONT_BODY, "", SIZE_SMALL)

    for line in ai_text.split("\n"):
        line = line.strip()
        if not line:
            pdf.ln(2)
            continue

        if pdf.get_y() > 275:
            pdf.add_page()

        # Sempre resetar X para margem esquerda
        pdf.set_x(MARGIN_LEFT)

        # Bold headers
        if line.startswith("**") and line.endswith("**"):
            pdf.set_font(FONT_BODY, "B", SIZE_SMALL)
            pdf.multi_cell(CONTENT_WIDTH, 5, line.replace("**", ""))
            pdf.set_font(FONT_BODY, "", SIZE_SMALL)
        elif line.startswith("## ") or line.startswith("# "):
            pdf.set_font(FONT_BODY, "B", SIZE_SMALL)
            pdf.multi_cell(CONTENT_WIDTH, 5, line.lstrip("#").strip())
            pdf.set_font(FONT_BODY, "", SIZE_SMALL)
        elif line.startswith("- ") or line.startswith("* "):
            clean = line[2:].replace("**", "")
            pdf.cell(5, 4, "-")
            pdf.multi_cell(CONTENT_WIDTH - 5, 4, f" {clean}")
        else:
            clean = line.replace("**", "")
            pdf.multi_cell(CONTENT_WIDTH, 4, clean)


def add_asset_page(pdf: FPDF, analysis: Dict, ai_text: str):
    """Adiciona página completa de análise de um ativo."""
    pdf.add_page()
    _asset_header(pdf, analysis)

    # Linha separadora
    pdf.set_draw_color(*VERDE_ESCURO)
    pdf.set_line_width(0.3)
    pdf.line(MARGIN_LEFT, pdf.get_y(), MARGIN_LEFT + CONTENT_WIDTH, pdf.get_y())
    pdf.ln(4)

    _metrics_grid(pdf, analysis)
    _fundamentals_section(pdf, analysis)

    pdf.ln(3)
    _ai_analysis_section(pdf, ai_text)
