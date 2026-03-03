"""Orquestrador de montagem do PDF final."""

import tempfile
from pathlib import Path
from typing import Dict, Any, List

from fpdf import FPDF

from agente_investimentos.report.styles import (
    MARGIN_LEFT, MARGIN_RIGHT, MARGIN_TOP, FONT_BODY, SIZE_TINY, CINZA_MEDIO, TEXTO,
)
from agente_investimentos.report.cover_page import add_cover_page
from agente_investimentos.report.sections import (
    add_executive_summary,
    add_overview_table,
    add_consolidated_section,
    add_sources_section,
    add_disclaimer,
)
from agente_investimentos.report.asset_pages import add_asset_page
from agente_investimentos.report.charts import (
    create_sector_pie,
    create_type_bars,
    create_return_bars,
)
from agente_investimentos.pdf_reader.models import PortfolioData
from agente_investimentos.config import PASTA_SAIDA


class ReportBuilder:
    """Monta o relatório PDF completo."""

    def __init__(self, portfolio: PortfolioData, portfolio_analysis: Dict,
                 asset_analyses: List[Dict], ai_texts: Dict[str, str],
                 portfolio_ai: str, sources: List[Dict]):
        self.portfolio = portfolio
        self.portfolio_analysis = portfolio_analysis
        self.asset_analyses = asset_analyses
        self.ai_texts = ai_texts
        self.portfolio_ai = portfolio_ai
        self.sources = sources
        self.temp_dir = Path(tempfile.mkdtemp())

    def _generate_charts(self) -> Dict[str, Path]:
        """Gera todos os gráficos necessários."""
        charts = {}

        # Gráfico de distribuição por tipo
        type_data = self.portfolio_analysis.get("distribuição_tipo", {})
        if type_data:
            charts["type_bars"] = create_type_bars(
                type_data, self.temp_dir / "type_bars.png"
            )

        # Gráfico de setor
        sector_data = self.portfolio_analysis.get("distribuição_setor", {})
        if sector_data:
            charts["sector_pie"] = create_sector_pie(
                sector_data, self.temp_dir / "sector_pie.png"
            )

        # Gráficos de rentabilidade
        if self.portfolio.assets:
            charts["return_mes"] = create_return_bars(
                self.portfolio.assets, self.temp_dir / "return_mes.png", "mês"
            )
            charts["return_ano"] = create_return_bars(
                self.portfolio.assets, self.temp_dir / "return_ano.png", "ano"
            )

        return charts

    def build(self) -> Path:
        """Monta e salva o PDF completo. Retorna caminho do arquivo."""
        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=20)
        pdf.set_margins(MARGIN_LEFT, MARGIN_TOP, MARGIN_RIGHT)

        # 1. Capa
        add_cover_page(pdf, self.portfolio.client_code, self.portfolio.data_referencia)

        # 2. Sumário executivo
        add_executive_summary(pdf, self.portfolio_ai, self.portfolio_analysis)

        # 3. Tabela visão geral
        add_overview_table(pdf, self.portfolio.assets)

        # 4. Seção consolidada com gráficos
        charts = self._generate_charts()
        add_consolidated_section(pdf, self.portfolio_analysis, charts)

        # 5. Páginas individuais dos ativos
        for analysis in self.asset_analyses:
            ticker = analysis.get("ticker", "")
            ai_text = self.ai_texts.get(ticker, "")
            add_asset_page(pdf, analysis, ai_text)

        # 6. Fontes
        add_sources_section(pdf, self.sources)

        # 7. Disclaimer
        add_disclaimer(pdf)

        # Salvar
        output_name = f"{self.portfolio.client_code}_Análise_de_Carteira_XP.pdf"
        output_path = PASTA_SAIDA / output_name
        pdf.output(str(output_path))

        # Cleanup temp
        for f in self.temp_dir.iterdir():
            f.unlink()
        self.temp_dir.rmdir()

        return output_path
