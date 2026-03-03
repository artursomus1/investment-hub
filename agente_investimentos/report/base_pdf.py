"""Componentes PDF compartilhados entre relatórios Somus Capital."""

from datetime import datetime
from pathlib import Path

from fpdf import FPDF

from agente_investimentos.report.styles import (
    VERDE_ESCURO, BRANCO, TEXTO, CINZA_MEDIO,
    FONT_BODY, SIZE_TINY, SIZE_SMALL,
    MARGIN_LEFT, CONTENT_WIDTH,
)
from agente_investimentos.utils.formatters import sanitize_text

# Meses em português para data formal
_MESES_PT = {
    1: "Janeiro", 2: "Fevereiro", 3: "Marco", 4: "Abril",
    5: "Maio", 6: "Junho", 7: "Julho", 8: "Agosto",
    9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro",
}


def _data_completa() -> str:
    """Retorna data atual no formato '22 de Fevereiro de 2026'."""
    now = datetime.now()
    return f"{now.day:02d} de {_MESES_PT[now.month]} de {now.year}"


class SomusPDF(FPDF):
    """PDF com footer formal: logo Somus Capital + número de página."""

    def __init__(self, logo_path: str = None):
        super().__init__()
        self._logo_path = logo_path
        self._skip_footer_pages = set()

    def skip_footer_on_current_page(self):
        """Marca página atual para não exibir footer."""
        self._skip_footer_pages.add(self.page_no())

    def footer(self):
        if self.page_no() in self._skip_footer_pages:
            return

        # Posiciona a 13mm do fundo (era -11)
        self.set_y(-13)

        # Linha separadora fina
        self.set_draw_color(*CINZA_MEDIO)
        self.set_line_width(0.15)
        self.line(MARGIN_LEFT, self.get_y(), MARGIN_LEFT + CONTENT_WIDTH, self.get_y())

        y_pos = self.get_y() + 1

        # Logo no canto inferior esquerdo (h=8, era 6)
        if self._logo_path and Path(self._logo_path).exists():
            try:
                self.image(self._logo_path, x=MARGIN_LEFT, y=y_pos, h=8)
            except Exception:
                self.set_xy(MARGIN_LEFT, y_pos)
                self.set_font(FONT_BODY, "B", 5.5)
                self.set_text_color(*VERDE_ESCURO)
                self.cell(30, 8, "SOMUS CAPITAL")
        else:
            self.set_xy(MARGIN_LEFT, y_pos)
            self.set_font(FONT_BODY, "B", 5.5)
            self.set_text_color(*VERDE_ESCURO)
            self.cell(30, 8, "SOMUS CAPITAL")

        # Número da página no canto direito (cell height 8, era 6)
        self.set_xy(MARGIN_LEFT, y_pos)
        self.set_font(FONT_BODY, "", 6)
        self.set_text_color(*CINZA_MEDIO)
        self.cell(CONTENT_WIDTH, 8, f"Página {self.page_no()}", align="R")


def check_space(pdf: FPDF, needed: float = 30):
    """Adiciona nova página se não houver espaço suficiente."""
    if pdf.get_y() > 282 - needed:
        pdf.add_page()


def section_bar(pdf: FPDF, title: str, color=VERDE_ESCURO):
    """Barra de seção compacta."""
    pdf.set_fill_color(*color)
    pdf.set_text_color(*BRANCO)
    pdf.set_font(FONT_BODY, "B", SIZE_SMALL)
    pdf.cell(CONTENT_WIDTH, 6, f"  {title}", fill=True, new_x="LMARGIN", new_y="NEXT")
    pdf.ln(1)
    pdf.set_text_color(*TEXTO)


def render_ai_text(pdf: FPDF, text: str):
    """Renderiza texto AI com markdown básico, compacto."""
    text = sanitize_text(text)
    pdf.set_font(FONT_BODY, "", SIZE_TINY + 1)
    for line in text.split("\n"):
        line = line.strip()
        if not line:
            pdf.ln(1)
            continue
        if pdf.get_y() > 272:
            pdf.add_page()

        # Sempre resetar X para margem esquerda antes de cada linha
        pdf.set_x(MARGIN_LEFT)

        clean = line.replace("**", "").replace("##", "").replace("# ", "")

        # Headers/titles in bold
        if line.startswith(("**", "## ", "# ")) or (line[0:1].isdigit() and ". " in line[:4]):
            pdf.set_font(FONT_BODY, "B", SIZE_TINY + 1)
            pdf.multi_cell(CONTENT_WIDTH, 3.5, clean)
            pdf.set_font(FONT_BODY, "", SIZE_TINY + 1)
        elif line.startswith(("- ", "* ", "• ")):
            bullet_text = clean.lstrip("-*• ").strip()
            pdf.cell(4, 3.5, "-")
            pdf.multi_cell(CONTENT_WIDTH - 4, 3.5, f" {bullet_text}")
        else:
            pdf.multi_cell(CONTENT_WIDTH, 3.5, clean)
