"""Página de capa do relatório Somus Capital."""

from fpdf import FPDF
from pathlib import Path

from agente_investimentos.report.styles import (
    VERDE_ESCURO, BRANCO, FONT_TITLE, FONT_BODY,
    SIZE_TITLE, SIZE_BODY, SIZE_SMALL,
)
from agente_investimentos.config import LOGO_PATH


def add_cover_page(pdf: FPDF, client_code: str, ref_date: str):
    """Adiciona página de capa com identidade visual Somus Capital."""
    pdf.add_page()

    # Fundo verde escuro
    pdf.set_fill_color(*VERDE_ESCURO)
    pdf.rect(0, 0, 210, 297, "F")

    # Logo (se disponível)
    if LOGO_PATH.exists():
        try:
            pdf.image(str(LOGO_PATH), x=45, y=50, w=120)
        except Exception:
            # Fallback: texto
            pdf.set_text_color(*BRANCO)
            pdf.set_font(FONT_TITLE, "B", 28)
            pdf.set_xy(0, 60)
            pdf.cell(210, 15, "SOMUS CAPITAL", align="C")
    else:
        pdf.set_text_color(*BRANCO)
        pdf.set_font(FONT_TITLE, "B", 28)
        pdf.set_xy(0, 60)
        pdf.cell(210, 15, "SOMUS CAPITAL", align="C")

    # Linha separadora
    pdf.set_draw_color(*BRANCO)
    pdf.set_line_width(0.5)
    pdf.line(50, 120, 160, 120)

    # Título do relatório
    pdf.set_text_color(*BRANCO)
    pdf.set_font(FONT_TITLE, "B", SIZE_TITLE)
    pdf.set_xy(0, 135)
    pdf.cell(210, 12, "Relatório de Análise", align="C")

    pdf.set_font(FONT_TITLE, "B", 20)
    pdf.set_xy(0, 150)
    pdf.cell(210, 12, "de Carteira", align="C")

    # Código do cliente
    pdf.set_font(FONT_BODY, "", SIZE_BODY + 2)
    pdf.set_xy(0, 185)
    pdf.cell(210, 8, f"Cliente: {client_code}", align="C")

    # Data de referência
    if ref_date:
        pdf.set_font(FONT_BODY, "", SIZE_BODY)
        pdf.set_xy(0, 198)
        pdf.cell(210, 8, f"Referência: {ref_date}", align="C")

    # Rodapé
    pdf.set_font(FONT_BODY, "", SIZE_SMALL)
    pdf.set_xy(0, 270)
    pdf.cell(210, 5, "Documento gerado automaticamente por Agente de Investimentos", align="C")
    pdf.set_xy(0, 276)
    pdf.cell(210, 5, "Somus Capital - Assessoria de Investimentos", align="C")
