"""Construtor do relatório PDF detalhado por setor - layout compacto e formal."""

import tempfile
from pathlib import Path
from typing import Dict, List

from fpdf import FPDF

from agente_investimentos.report.styles import (
    VERDE_ESCURO, AZUL, BRANCO, TEXTO, FUNDO_CLARO, CINZA_MEDIO, VERDE_CLARO,
    FONT_TITLE, FONT_BODY, SIZE_TITLE, SIZE_SECTION, SIZE_BODY, SIZE_SMALL, SIZE_TINY,
    MARGIN_LEFT, MARGIN_RIGHT, MARGIN_TOP, CONTENT_WIDTH,
)
from agente_investimentos.report.charts import (
    create_price_line_chart,
    create_dividend_bar_chart,
)
from agente_investimentos.report.sections import add_disclaimer
from agente_investimentos.report.base_pdf import (
    SomusPDF, _data_completa, check_space, section_bar, render_ai_text,
)
from agente_investimentos.utils.formatters import format_brl, format_percent, sanitize_text
from agente_investimentos.pdf_reader.models import PortfolioData
from agente_investimentos.config import PASTA_SAIDA, LOGO_PATH

# Cores adicionais para setores
_SETOR_COLOR_MAP = {
    "Bancos e Financeiro": (24, 99, 220),
    "Energia e Utilities": (0, 128, 85),
    "Petroleo, Gas e Mineracao": (100, 60, 20),
    "Varejo e Consumo": (230, 126, 34),
    "Saude": (231, 76, 60),
    "Tecnologia e Telecom": (52, 152, 219),
    "Construcao e Imobiliario": (155, 89, 182),
    "Transporte e Logistica": (52, 73, 94),
    "Agronegocio": (39, 174, 96),
    "Papel e Celulose": (22, 160, 133),
    "Siderurgia": (127, 140, 141),
    "Educacao": (241, 196, 15),
}


def _get_sector_color(sector_name: str) -> tuple:
    """Retorna cor RGB para um setor."""
    for key, color in _SETOR_COLOR_MAP.items():
        if key in sector_name:
            return color
    if "Imobiliario" in sector_name:
        return AZUL
    if "RF" in sector_name or "Renda Fixa" in sector_name:
        return CINZA_MEDIO
    if "Fundo" in sector_name:
        return VERDE_CLARO
    return VERDE_ESCURO


class DetailedReportBuilder:
    """Monta o relatório PDF detalhado com análise por setor."""

    def __init__(self, portfolio: PortfolioData,
                 asset_analyses: List[Dict],
                 deep_ai_texts: Dict[str, str],
                 sources: List[Dict],
                 sector_ai_texts: Dict[str, str] = None,
                 portfolio_analysis: Dict = None):
        self.portfolio = portfolio
        self.asset_analyses = asset_analyses
        self.deep_ai_texts = deep_ai_texts
        self.sources = sources
        self.sector_ai_texts = sector_ai_texts or {}
        self.portfolio_analysis = portfolio_analysis or {}
        self.temp_dir = Path(tempfile.mkdtemp())

        # Indexar análises por ticker para busca rápida
        self._analysis_by_ticker = {a.get("ticker", ""): a for a in asset_analyses}

    def _add_cover(self, pdf: SomusPDF):
        """Capa do relatório detalhado."""
        pdf.add_page()
        pdf.skip_footer_on_current_page()
        pdf.set_fill_color(*VERDE_ESCURO)
        pdf.rect(0, 0, 210, 297, "F")

        if LOGO_PATH.exists():
            try:
                pdf.image(str(LOGO_PATH), x=45, y=50, w=120)
            except Exception:
                pdf.set_text_color(*BRANCO)
                pdf.set_font(FONT_TITLE, "B", 28)
                pdf.set_xy(0, 60)
                pdf.cell(210, 15, "SOMUS CAPITAL", align="C")
        else:
            pdf.set_text_color(*BRANCO)
            pdf.set_font(FONT_TITLE, "B", 28)
            pdf.set_xy(0, 60)
            pdf.cell(210, 15, "SOMUS CAPITAL", align="C")

        pdf.set_draw_color(*BRANCO)
        pdf.set_line_width(0.5)
        pdf.line(50, 120, 160, 120)

        pdf.set_text_color(*BRANCO)
        pdf.set_font(FONT_TITLE, "B", SIZE_TITLE)
        pdf.set_xy(0, 135)
        pdf.cell(210, 12, sanitize_text("Análise Detalhada"), align="C")
        pdf.set_font(FONT_TITLE, "B", 20)
        pdf.set_xy(0, 150)
        pdf.cell(210, 12, "por Setor", align="C")

        # Subtítulo
        pdf.set_font(FONT_BODY, "", SIZE_BODY + 1)
        pdf.set_xy(0, 168)
        pdf.cell(210, 7, "Relatório Claudinho - Agente de investimentos | Somus Capital", align="C")

        pdf.set_font(FONT_BODY, "", SIZE_BODY + 2)
        pdf.set_xy(0, 185)
        pdf.cell(210, 8, f"Cliente: {self.portfolio.client_code}", align="C")

        # Data de geração completa
        pdf.set_font(FONT_BODY, "", SIZE_BODY)
        pdf.set_xy(0, 198)
        data_text = sanitize_text(f"Relatório gerado em: {_data_completa()}")
        pdf.cell(210, 8, data_text, align="C")

        n_setores = len(self.portfolio_analysis.get("distribuição_setor", {}))
        pdf.set_font(FONT_BODY, "", SIZE_SMALL)
        pdf.set_xy(0, 265)
        pdf.cell(210, 5, f"{self.portfolio.num_assets} ativos em {n_setores} setores", align="C")

    def _add_sector_overview(self, pdf: FPDF):
        """Tabela de visão geral setorial."""
        pdf.add_page()
        section_bar(pdf, sanitize_text("VISAO GERAL DA CARTEIRA POR SETOR"))

        dist_setor = self.portfolio_analysis.get("distribuição_setor", {})
        if not dist_setor:
            pdf.set_font(FONT_BODY, "", SIZE_BODY)
            pdf.cell(CONTENT_WIDTH, 8, "Dados setoriais indisponíveis.", new_x="LMARGIN", new_y="NEXT")
            return

        # Cabeçalho da tabela
        col_widths = [55, 15, 30, 20, 30, 30]  # Setor, Qtd, Saldo, Aloc%, Mês%, Ano%
        headers = ["Setor", "Qtd", "Saldo", "Aloc.%", "Rent.Mês%", "Rent.Ano%"]

        pdf.set_fill_color(*VERDE_ESCURO)
        pdf.set_text_color(*BRANCO)
        pdf.set_font(FONT_BODY, "B", SIZE_TINY)

        for i, (header, w) in enumerate(zip(headers, col_widths)):
            align = "L" if i == 0 else "C"
            pdf.cell(w, 6, f" {header}", fill=True, align=align)
        pdf.ln()

        # Linhas da tabela
        pdf.set_text_color(*TEXTO)
        pdf.set_font(FONT_BODY, "", SIZE_TINY)
        alt = False

        for setor_name, dados in dist_setor.items():
            if alt:
                pdf.set_fill_color(*FUNDO_CLARO)
            else:
                pdf.set_fill_color(*BRANCO)

            setor_display = sanitize_text(setor_name)[:28]
            pdf.cell(col_widths[0], 5.5, f" {setor_display}", fill=True)
            pdf.cell(col_widths[1], 5.5, str(dados["count"]), fill=True, align="C")
            pdf.cell(col_widths[2], 5.5, format_brl(dados["saldo"]), fill=True, align="C")
            pdf.cell(col_widths[3], 5.5, f"{dados['alocacao']:.1f}%", fill=True, align="C")
            pdf.cell(col_widths[4], 5.5, f"{dados['rent_mes_ponderada']:+.2f}%", fill=True, align="C")
            pdf.cell(col_widths[5], 5.5, f"{dados['rent_ano_ponderada']:+.2f}%", fill=True, align="C")
            pdf.ln()
            alt = not alt

            if pdf.get_y() > 268:
                pdf.add_page()

        pdf.ln(1)

        # Total
        total_bruto = self.portfolio_analysis.get("total_bruto", 0)
        pdf.set_font(FONT_BODY, "B", SIZE_TINY)
        pdf.set_fill_color(*FUNDO_CLARO)
        pdf.cell(col_widths[0], 6, " TOTAL", fill=True)
        pdf.cell(col_widths[1], 6, str(self.portfolio_analysis.get("num_ativos", 0)), fill=True, align="C")
        pdf.cell(col_widths[2], 6, format_brl(total_bruto), fill=True, align="C")
        pdf.cell(col_widths[3], 6, "100%", fill=True, align="C")
        rent_mes = self.portfolio_analysis.get("rent_mes_ponderada", 0)
        rent_ano = self.portfolio_analysis.get("rent_ano_ponderada", 0)
        pdf.cell(col_widths[4], 6, f"{rent_mes:+.2f}%", fill=True, align="C")
        pdf.cell(col_widths[5], 6, f"{rent_ano:+.2f}%", fill=True, align="C")
        pdf.ln(4)

    def _add_sector_header(self, pdf: FPDF, sector_name: str, sector_data: dict):
        """Header de setor com barra colorida."""
        pdf.add_page()
        color = _get_sector_color(sector_name)

        # Barra do setor
        pdf.set_fill_color(*color)
        pdf.set_text_color(*BRANCO)
        pdf.set_font(FONT_TITLE, "B", SIZE_SECTION)

        sector_display = sanitize_text(sector_name)
        aloc = sector_data.get("alocacao", 0)
        saldo = sector_data.get("saldo", 0)
        count = sector_data.get("count", 0)

        pdf.cell(CONTENT_WIDTH, 10, f"  {sector_display}", fill=True, new_x="LMARGIN", new_y="NEXT")

        # Sub-info do setor
        pdf.set_fill_color(*(min(c + 30, 255) for c in color))
        pdf.set_font(FONT_BODY, "B", SIZE_SMALL)
        info = f"  {count} ativo(s) | {format_brl(saldo)} | {aloc:.1f}% da carteira"
        rent_mes = sector_data.get("rent_mes_ponderada", 0)
        rent_ano = sector_data.get("rent_ano_ponderada", 0)
        info += f" | Mês: {rent_mes:+.2f}% | Ano: {rent_ano:+.2f}%"
        pdf.cell(CONTENT_WIDTH, 7, info, fill=True, new_x="LMARGIN", new_y="NEXT")

        pdf.set_text_color(*TEXTO)
        pdf.ln(2)

    def _add_sector_analysis(self, pdf: FPDF, sector_name: str, ai_text: str):
        """Análise IA do setor."""
        if not ai_text:
            return
        check_space(pdf, 25)
        color = _get_sector_color(sector_name)
        section_bar(pdf, sanitize_text(f"ANÁLISE DO SETOR: {sector_name}"), color=color)
        render_ai_text(pdf, ai_text)
        pdf.ln(1)

    def _add_upside_box(self, pdf: FPDF, fund: dict, tipo: str):
        """Caixa de potencial de alta/sensibilidade."""
        dist_high = fund.get("distancia_52w_high")
        vol = fund.get("volatilidade")
        sens = fund.get("score_sensibilidade")

        if dist_high is None and vol is None:
            return

        check_space(pdf, 20)

        # Caixa com borda
        y_start = pdf.get_y()
        pdf.set_draw_color(*AZUL)
        pdf.set_line_width(0.3)

        pdf.set_fill_color(235, 245, 255)
        pdf.set_font(FONT_BODY, "B", SIZE_TINY)
        pdf.set_text_color(*AZUL)
        pdf.cell(CONTENT_WIDTH, 5, "  POTENCIAL E SENSIBILIDADE", fill=True, new_x="LMARGIN", new_y="NEXT")

        pdf.set_text_color(*TEXTO)
        pdf.set_font(FONT_BODY, "", SIZE_TINY)
        items = []
        if dist_high is not None:
            high = fund.get("fiftyTwoWeekHigh")
            label = f"Dist. topo 52s: {dist_high:+.1f}%"
            if high:
                label += f" (max: R$ {high:.2f})"
            items.append(label)

        dist_low = fund.get("distancia_52w_low")
        if dist_low is not None:
            low = fund.get("fiftyTwoWeekLow")
            label = f"Acima minima 52s: +{dist_low:.1f}%"
            if low:
                label += f" (min: R$ {low:.2f})"
            items.append(label)

        if vol is not None:
            items.append(f"Volatilidade anualizada: {vol:.1f}%")
        if sens:
            items.append(f"Sensibilidade: {sens}")

        pdf.set_fill_color(245, 250, 255)
        for item in items:
            pdf.cell(CONTENT_WIDTH, 4, f"  - {item}", fill=True, new_x="LMARGIN", new_y="NEXT")

        # Borda da caixa
        y_end = pdf.get_y()
        pdf.rect(MARGIN_LEFT, y_start, CONTENT_WIDTH, y_end - y_start)
        pdf.ln(2)

    def _add_asset_section(self, pdf: FPDF, analysis: Dict, ai_text: str, is_first_in_sector: bool = False):
        """Seção completa de um ativo - compacta, máximo conteúdo."""
        ticker = analysis.get("ticker", "")
        tipo = analysis.get("tipo", "")
        nome = analysis.get("nome", "")
        fund = analysis.get("fundamentals", {})

        # Nova página se não for o primeiro do setor (o primeiro já tem header)
        if not is_first_in_sector:
            pdf.add_page()
        else:
            check_space(pdf, 60)

        tipo_colors = {"Acao": VERDE_ESCURO, "FII": AZUL, "RF": CINZA_MEDIO, "Fundo": VERDE_CLARO}
        color = tipo_colors.get(tipo, CINZA_MEDIO)

        # Badge + Ticker
        pdf.set_fill_color(*color)
        pdf.set_text_color(*BRANCO)
        pdf.set_font(FONT_BODY, "B", SIZE_SMALL)
        pdf.cell(18, 7, f" {tipo} ", fill=True)
        pdf.set_text_color(*TEXTO)
        pdf.set_font(FONT_TITLE, "B", SIZE_SECTION)
        pdf.cell(5, 7, "")
        pdf.cell(0, 7, ticker, new_x="LMARGIN", new_y="NEXT")

        nome_display = sanitize_text(nome[:75] if len(nome) > 75 else nome)
        pdf.set_font(FONT_BODY, "", SIZE_TINY + 1)
        pdf.set_text_color(*CINZA_MEDIO)
        nome_longo = sanitize_text(fund.get("nome_longo", nome_display) or nome_display)
        pdf.cell(CONTENT_WIDTH, 4, nome_longo[:80] if nome_longo else nome_display,
                 new_x="LMARGIN", new_y="NEXT")

        # Separador
        pdf.set_draw_color(*color)
        pdf.set_line_width(0.5)
        pdf.line(MARGIN_LEFT, pdf.get_y() + 1, MARGIN_LEFT + CONTENT_WIDTH, pdf.get_y() + 1)
        pdf.ln(3)

        # === MÉTRICAS COMPACTAS (2 linhas) ===
        pdf.set_text_color(*TEXTO)
        metrics_row1 = [
            ("Saldo", format_brl(analysis["saldo_bruto"])),
            ("Aloc.", format_percent(analysis["alocacao"])),
            ("Rent.Mês", format_percent(analysis["rent_mes"])),
            ("%CDI Mês", format_percent(analysis["cdi_mes"])),
            ("Rent.Ano", format_percent(analysis["rent_ano"])),
            ("%CDI Ano", format_percent(analysis["cdi_ano"])),
        ]

        col_w = CONTENT_WIDTH / 6
        y = pdf.get_y()
        for i, (label, value) in enumerate(metrics_row1):
            x = MARGIN_LEFT + i * col_w
            pdf.set_xy(x, y)
            pdf.set_font(FONT_BODY, "", 5.5)
            pdf.set_text_color(*CINZA_MEDIO)
            pdf.cell(col_w, 4, label, align="C")
            pdf.set_xy(x, y + 4)
            pdf.set_font(FONT_BODY, "B", SIZE_TINY + 1)
            pdf.set_text_color(*TEXTO)
            pdf.cell(col_w, 5, value, align="C")

        pdf.set_xy(MARGIN_LEFT, y + 11)

        # Métricas fundamentalistas (se existem)
        if fund:
            fund_items = []
            if fund.get("preço") is not None:
                fund_items.append(f"Preco: R$ {fund['preço']:.2f}")
            if fund.get("p_l") is not None:
                fund_items.append(f"P/L: {fund['p_l']:.2f}")
            if fund.get("p_vp") is not None:
                fund_items.append(f"P/VP: {fund['p_vp']:.2f}")
            if fund.get("dividend_yield") is not None:
                fund_items.append(f"DY: {fund['dividend_yield']:.2f}%")
            if fund.get("roe") is not None:
                fund_items.append(f"ROE: {fund['roe']:.1f}%")
            if fund.get("ebit_margin") is not None:
                fund_items.append(f"Mg.EBIT: {fund['ebit_margin']:.1f}%")
            if fund.get("net_margin") is not None:
                fund_items.append(f"Mg.Liq: {fund['net_margin']:.1f}%")
            if fund.get("divida_líquida_ebitda") is not None:
                fund_items.append(f"DL/EBITDA: {fund['divida_líquida_ebitda']:.2f}")

            if fund_items:
                pdf.set_fill_color(*FUNDO_CLARO)
                pdf.set_font(FONT_BODY, "", SIZE_TINY)
                pdf.set_text_color(*TEXTO)
                line = " | ".join(fund_items)
                pdf.cell(CONTENT_WIDTH, 5, line, fill=True, new_x="LMARGIN", new_y="NEXT")

            setor = fund.get("setor", "")
            industria = fund.get("industria", "")
            if setor and setor != "N/D":
                pdf.set_font(FONT_BODY, "I", SIZE_TINY)
                pdf.set_text_color(*CINZA_MEDIO)
                setor_text = sanitize_text(f"Setor: {setor}")
                if industria and industria != "N/D":
                    setor_text += sanitize_text(f" | {industria}")
                pdf.cell(CONTENT_WIDTH, 4, setor_text, new_x="LMARGIN", new_y="NEXT")

        pdf.ln(2)

        # === CAIXA DE POTENCIAL (para ações e FIIs) ===
        if tipo in ("Acao", "FII") and fund:
            self._add_upside_box(pdf, fund, tipo)

        # === GRÁFICOS ===
        hist = analysis.get("historical_prices", [])
        divs = analysis.get("dividends", [])
        has_price_chart = hist and tipo in ("Acao", "FII")
        has_div_chart = divs and tipo in ("Acao", "FII")

        if has_price_chart:
            chart_path = self.temp_dir / f"price_{ticker}.png"
            create_price_line_chart(ticker, hist, chart_path)
            if chart_path.exists():
                check_space(pdf, 47)
                pdf.image(str(chart_path), x=MARGIN_LEFT, w=CONTENT_WIDTH, h=42)
                pdf.ln(44)

        if has_div_chart:
            chart_path = self.temp_dir / f"div_{ticker}.png"
            create_dividend_bar_chart(ticker, divs, chart_path)
            if chart_path.exists():
                check_space(pdf, 42)
                pdf.image(str(chart_path), x=MARGIN_LEFT, w=CONTENT_WIDTH, h=36)
                pdf.ln(38)

        # === ANÁLISE IA APROFUNDADA (inclui resumo de notícias) ===
        if ai_text and "indisponível" not in ai_text.lower() and "indisponível" not in ai_text.lower():
            check_space(pdf, 25)
            section_bar(pdf, sanitize_text("ANÁLISE IA APROFUNDADA (GEMINI)"))
            render_ai_text(pdf, ai_text)

        # === FONTES DE NOTÍCIAS (compacto, após análise IA) ===
        news = analysis.get("news", [])
        if news:
            fontes = []
            for n in news:
                f = n.get("fonte", "")
                if f and f not in fontes:
                    fontes.append(f)
            if fontes:
                pdf.ln(1)
                pdf.set_x(MARGIN_LEFT)
                pdf.set_font(FONT_BODY, "I", SIZE_TINY)
                pdf.set_text_color(*CINZA_MEDIO)
                src_text = sanitize_text(f"Fontes de notícias: {', '.join(fontes[:6])}")
                pdf.cell(CONTENT_WIDTH, 3.5, src_text, new_x="LMARGIN", new_y="NEXT")
                pdf.set_text_color(*TEXTO)

    def build(self) -> Path:
        """Monta e salva o PDF detalhado organizado por setor."""
        logo = str(LOGO_PATH) if LOGO_PATH.exists() else None
        pdf = SomusPDF(logo_path=logo)
        pdf.set_auto_page_break(auto=True, margin=20)
        pdf.set_margins(MARGIN_LEFT, MARGIN_TOP, MARGIN_RIGHT)

        # 1. Capa
        self._add_cover(pdf)

        # 2. Visão geral da carteira por setor
        self._add_sector_overview(pdf)

        # 3. Para cada setor (ordenado por alocação)
        dist_setor = self.portfolio_analysis.get("distribuição_setor", {})

        for sector_name, sector_data in dist_setor.items():
            # 3a. Header do setor
            self._add_sector_header(pdf, sector_name, sector_data)

            # 3b. Análise IA do setor
            sector_ai = self.sector_ai_texts.get(sector_name, "")
            if sector_ai:
                self._add_sector_analysis(pdf, sector_name, sector_ai)

            # 3c. Ativos do setor
            ativos_setor = sector_data.get("ativos", [])
            for idx, ativo_info in enumerate(ativos_setor):
                ticker = ativo_info.get("ticker", "")
                analysis = self._analysis_by_ticker.get(ticker)
                if not analysis:
                    continue

                ai_text = self.deep_ai_texts.get(ticker, "")
                is_first = (idx == 0)
                self._add_asset_section(pdf, analysis, ai_text, is_first_in_sector=is_first)

        # 4. Disclaimer
        add_disclaimer(pdf)

        # Salvar
        output_name = f"{self.portfolio.client_code}_Análise_Detalhada_XP.pdf"
        output_path = PASTA_SAIDA / output_name
        pdf.output(str(output_path))

        # Cleanup
        for f in self.temp_dir.iterdir():
            f.unlink()
        self.temp_dir.rmdir()

        return output_path
