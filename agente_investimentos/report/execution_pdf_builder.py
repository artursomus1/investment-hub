"""Construtor do relatório PDF de execução - máximo 3 páginas, foco em ação."""

from pathlib import Path
from typing import Dict, List

from fpdf import FPDF

from agente_investimentos.report.styles import (
    VERDE_ESCURO, AZUL, BRANCO, TEXTO, FUNDO_CLARO, CINZA_MEDIO,
    FONT_TITLE, FONT_BODY, SIZE_SECTION, SIZE_BODY, SIZE_SMALL, SIZE_TINY,
    MARGIN_LEFT, MARGIN_RIGHT, MARGIN_TOP, CONTENT_WIDTH,
)
from agente_investimentos.report.base_pdf import (
    SomusPDF, _data_completa, check_space, section_bar, render_ai_text,
)
from agente_investimentos.utils.formatters import format_brl, format_percent, sanitize_text
from agente_investimentos.pdf_reader.models import PortfolioData
from agente_investimentos.config import PASTA_SAIDA, LOGO_PATH

# Vermelho para riscos
_VERMELHO = (200, 40, 40)
_LARANJA = (220, 140, 20)


class ExecutionReportBuilder:
    """Monta relatório de execução (max 3 páginas) com diagnóstico e recomendações."""

    def __init__(self, portfolio: PortfolioData,
                 portfolio_analysis: Dict,
                 asset_analyses: List[Dict],
                 execution_ai: str,
                 macro: Dict):
        self.portfolio = portfolio
        self.portfolio_analysis = portfolio_analysis
        self.asset_analyses = asset_analyses
        self.execution_ai = execution_ai
        self.macro = macro

    def _add_compact_header(self, pdf: SomusPDF):
        """Header compacto: banner verde 42mm com logo + título + cliente + data."""
        pdf.add_page()
        pdf.skip_footer_on_current_page()

        # Banner verde escuro
        banner_h = 42
        pdf.set_fill_color(*VERDE_ESCURO)
        pdf.rect(0, 0, 210, banner_h, "F")

        # Logo no banner
        if LOGO_PATH.exists():
            try:
                pdf.image(str(LOGO_PATH), x=MARGIN_LEFT, y=6, h=12)
            except Exception:
                pdf.set_text_color(*BRANCO)
                pdf.set_font(FONT_TITLE, "B", 14)
                pdf.set_xy(MARGIN_LEFT, 8)
                pdf.cell(60, 10, "SOMUS CAPITAL")
        else:
            pdf.set_text_color(*BRANCO)
            pdf.set_font(FONT_TITLE, "B", 14)
            pdf.set_xy(MARGIN_LEFT, 8)
            pdf.cell(60, 10, "SOMUS CAPITAL")

        # Título principal
        pdf.set_text_color(*BRANCO)
        pdf.set_font(FONT_TITLE, "B", 16)
        pdf.set_xy(MARGIN_LEFT, 21)
        pdf.cell(CONTENT_WIDTH, 8, sanitize_text("RELATÓRIO DE EXECUÇÃO"), align="C")

        # Cliente + Data
        pdf.set_font(FONT_BODY, "", SIZE_SMALL)
        pdf.set_xy(MARGIN_LEFT, 30)
        data_text = sanitize_text(f"Cliente: {self.portfolio.client_code}  |  {_data_completa()}")
        pdf.cell(CONTENT_WIDTH, 6, data_text, align="C")

        pdf.set_xy(MARGIN_LEFT, banner_h + 3)

    def _add_kpis(self, pdf: FPDF):
        """5 caixas de KPIs: Patrimônio, Ativos, Rent.Mês, Rent.Ano, Concentração."""
        pa = self.portfolio_analysis
        hhi = pa.get("concentração_hhi", 0)
        nivel = pa.get("nivel_concentração", "N/D")

        kpis = [
            ("Patrimônio", format_brl(pa["total_bruto"])),
            ("Ativos", str(pa["num_ativos"])),
            ("Rent. Mês", f"{pa['rent_mes_ponderada']:+.2f}%"),
            ("Rent. Ano", f"{pa['rent_ano_ponderada']:+.2f}%"),
            ("Concentração", f"{nivel} ({hhi:.0f})"),
        ]

        box_w = CONTENT_WIDTH / 5
        y = pdf.get_y()

        for i, (label, value) in enumerate(kpis):
            x = MARGIN_LEFT + i * box_w

            # Label
            pdf.set_xy(x, y)
            pdf.set_fill_color(*FUNDO_CLARO)
            pdf.set_font(FONT_BODY, "", 5.5)
            pdf.set_text_color(*CINZA_MEDIO)
            pdf.cell(box_w - 1, 4, label, align="C", fill=True)

            # Value
            pdf.set_xy(x, y + 4)
            pdf.set_font(FONT_BODY, "B", SIZE_SMALL)
            pdf.set_text_color(*TEXTO)
            pdf.cell(box_w - 1, 6, value, align="C", fill=True)

        pdf.set_xy(MARGIN_LEFT, y + 12)

    def _add_risk_table(self, pdf: FPDF):
        """Tabela de principais riscos: ativos com flags de risco."""
        risk_rows = []
        for a in self.asset_analyses:
            ticker = a.get("ticker", "")
            aloc = a.get("alocacao", 0)
            rent_mes = a.get("rent_mes", 0)
            rent_ano = a.get("rent_ano", 0)
            fund = a.get("fundamentals", {})
            vol = fund.get("volatilidade")
            dl_ebitda = fund.get("divida_líquida_ebitda")

            flags = []
            if vol is not None and vol > 40:
                flags.append(f"Vol {vol:.0f}%")
            if aloc > 15:
                flags.append(f"Aloc {aloc:.1f}%")
            if dl_ebitda is not None and dl_ebitda > 3:
                flags.append(f"DL/EBITDA {dl_ebitda:.1f}")
            if rent_ano < -10:
                flags.append(f"Ano {rent_ano:+.1f}%")
            if rent_mes < -5:
                flags.append(f"Mês {rent_mes:+.1f}%")

            if flags:
                risk_rows.append((ticker, aloc, rent_mes, rent_ano, flags))

        if not risk_rows:
            return

        # Ordenar por número de flags (mais riscos primeiro)
        risk_rows.sort(key=lambda r: len(r[4]), reverse=True)
        risk_rows = risk_rows[:8]  # Máximo 8 linhas

        section_bar(pdf, "PRINCIPAIS RISCOS IDENTIFICADOS", color=_VERMELHO)

        # Cabeçalho da tabela
        cols = [("Ativo", 22), ("Aloc.%", 14), ("Mês%", 14), ("Ano%", 14), ("Flags de Risco", 116)]
        pdf.set_fill_color(*VERDE_ESCURO)
        pdf.set_text_color(*BRANCO)
        pdf.set_font(FONT_BODY, "B", SIZE_TINY)
        for label, w in cols:
            pdf.cell(w, 5, f" {label}", fill=True)
        pdf.ln()

        # Linhas
        pdf.set_text_color(*TEXTO)
        pdf.set_font(FONT_BODY, "", SIZE_TINY)
        for i, (ticker, aloc, rent_mes, rent_ano, flags) in enumerate(risk_rows):
            bg = FUNDO_CLARO if i % 2 == 0 else BRANCO
            pdf.set_fill_color(*bg)
            pdf.cell(cols[0][1], 4.5, f" {ticker}", fill=True)
            pdf.cell(cols[1][1], 4.5, f"{aloc:.1f}%", fill=True, align="C")

            # Colorir rent negativa
            if rent_mes < 0:
                pdf.set_text_color(*_VERMELHO)
            pdf.cell(cols[2][1], 4.5, f"{rent_mes:+.1f}%", fill=True, align="C")
            pdf.set_text_color(*TEXTO)

            if rent_ano < 0:
                pdf.set_text_color(*_VERMELHO)
            pdf.cell(cols[3][1], 4.5, f"{rent_ano:+.1f}%", fill=True, align="C")
            pdf.set_text_color(*TEXTO)

            flags_str = sanitize_text(" | ".join(flags))
            pdf.set_font(FONT_BODY, "B", SIZE_TINY)
            pdf.set_text_color(*_LARANJA)
            pdf.cell(cols[4][1], 4.5, f" {flags_str}", fill=True)
            pdf.set_text_color(*TEXTO)
            pdf.set_font(FONT_BODY, "", SIZE_TINY)
            pdf.ln()

        pdf.ln(2)

    def _add_sector_exposure(self, pdf: FPDF):
        """Barras horizontais de exposição setorial."""
        dist_setor = self.portfolio_analysis.get("distribuição_setor", {})
        if not dist_setor:
            return

        check_space(pdf, 35)
        section_bar(pdf, sanitize_text("EXPOSICAO SETORIAL"))

        max_aloc = max(d["alocacao"] for d in dist_setor.values()) if dist_setor else 1
        bar_max_w = CONTENT_WIDTH - 45  # espaço para label + valor

        pdf.set_font(FONT_BODY, "", SIZE_TINY)
        for setor, dados in list(dist_setor.items())[:10]:
            aloc = dados["alocacao"]
            bar_w = max((aloc / max_aloc) * bar_max_w, 2) if max_aloc > 0 else 2

            # Label do setor
            setor_display = sanitize_text(setor)[:22]
            pdf.set_text_color(*TEXTO)
            pdf.cell(35, 4, f" {setor_display}", new_x="END")

            # Barra
            y = pdf.get_y()
            x = pdf.get_x()
            pdf.set_fill_color(*VERDE_ESCURO)
            pdf.rect(x, y + 0.5, bar_w, 3, "F")

            # Valor
            pdf.set_xy(x + bar_w + 1, y)
            pdf.set_font(FONT_BODY, "B", SIZE_TINY)
            pdf.cell(20, 4, f"{aloc:.1f}%")
            pdf.set_font(FONT_BODY, "", SIZE_TINY)
            pdf.ln()

        pdf.ln(1)

    def _add_recommendations_pages(self, pdf: SomusPDF):
        """Páginas 2-3: recomendações AI + disclaimer inline."""
        pdf.add_page()

        section_bar(pdf, sanitize_text("RECOMENDAÇÕES DE EXECUÇÃO"), color=AZUL)

        if self.execution_ai and "indisponível" not in self.execution_ai.lower():
            render_ai_text(pdf, self.execution_ai)
        else:
            pdf.set_font(FONT_BODY, "", SIZE_BODY)
            pdf.multi_cell(CONTENT_WIDTH, 5, sanitize_text(
                "Análise de execução IA indisponível. Verifique a configuração do Gemini."
            ))

        # Disclaimer compacto inline (3 linhas)
        pdf.ln(3)
        check_space(pdf, 15)

        pdf.set_draw_color(*CINZA_MEDIO)
        pdf.set_line_width(0.15)
        pdf.line(MARGIN_LEFT, pdf.get_y(), MARGIN_LEFT + CONTENT_WIDTH, pdf.get_y())
        pdf.ln(1)

        pdf.set_font(FONT_BODY, "I", 5.5)
        pdf.set_text_color(*CINZA_MEDIO)
        pdf.multi_cell(CONTENT_WIDTH, 3, sanitize_text(
            "DISCLAIMER: Este relatório foi gerado automaticamente por IA (Google Gemini) e tem caráter "
            "exclusivamente informativo. Não constitui recomendacao de investimento. Rentabilidade passada "
            "não e garantia de resultados futuros. Consulte sempre um profissional qualificado antes de tomar decisoes."
        ))
        pdf.set_text_color(*TEXTO)

    def build(self) -> Path:
        """Monta e salva o PDF de execução (max 3 páginas)."""
        logo = str(LOGO_PATH) if LOGO_PATH.exists() else None
        pdf = SomusPDF(logo_path=logo)
        pdf.set_auto_page_break(auto=True, margin=20)
        pdf.set_margins(MARGIN_LEFT, MARGIN_TOP, MARGIN_RIGHT)

        # Página 1: Diagnóstico
        self._add_compact_header(pdf)
        self._add_kpis(pdf)
        self._add_risk_table(pdf)
        self._add_sector_exposure(pdf)

        # Páginas 2-3: Recomendações + Plano de Ação
        self._add_recommendations_pages(pdf)

        # Salvar
        output_name = f"{self.portfolio.client_code}_Relatório_Execução_XP.pdf"
        output_path = PASTA_SAIDA / output_name
        pdf.output(str(output_path))

        return output_path
