"""Seções do relatório: sumário executivo, visão geral, consolidado, fontes, disclaimer."""

from fpdf import FPDF
from typing import Dict, Any, List

from agente_investimentos.report.styles import (
    VERDE_ESCURO, AZUL, BRANCO, TEXTO, FUNDO_CLARO, CINZA_MEDIO,
    FONT_TITLE, FONT_BODY, SIZE_SECTION, SIZE_BODY, SIZE_SMALL, SIZE_TINY,
    MARGIN_LEFT, CONTENT_WIDTH,
)
from agente_investimentos.utils.formatters import format_brl, format_percent, sanitize_text


def _section_header(pdf: FPDF, title: str):
    """Adiciona cabeçalho de seção com fundo verde."""
    pdf.set_fill_color(*VERDE_ESCURO)
    pdf.set_text_color(*BRANCO)
    pdf.set_font(FONT_TITLE, "B", SIZE_SECTION)
    pdf.cell(CONTENT_WIDTH, 10, f"  {title}", fill=True, new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)
    pdf.set_text_color(*TEXTO)


def _check_page_space(pdf: FPDF, needed: float = 40):
    """Adiciona nova página se não houver espaço suficiente."""
    if pdf.get_y() > 297 - needed:
        pdf.add_page()


def add_executive_summary(pdf: FPDF, portfolio_ai: str, portfolio_analysis: Dict):
    """Adiciona página de sumário executivo."""
    pdf.add_page()
    _section_header(pdf, "SUMÁRIO EXECUTIVO")

    # Métricas chave em boxes
    pdf.set_font(FONT_BODY, "B", SIZE_BODY)
    metrics = [
        ("Patrimônio Total", format_brl(portfolio_analysis["total_bruto"])),
        ("Ativos", str(portfolio_analysis["num_ativos"])),
        ("Rent. Mês", format_percent(portfolio_analysis["rent_mes_ponderada"])),
        ("Rent. Ano", format_percent(portfolio_analysis["rent_ano_ponderada"])),
    ]

    box_w = CONTENT_WIDTH / 4
    x_start = MARGIN_LEFT
    for i, (label, value) in enumerate(metrics):
        x = x_start + i * box_w
        pdf.set_xy(x, pdf.get_y())
        pdf.set_fill_color(*FUNDO_CLARO)
        pdf.set_font(FONT_BODY, "", SIZE_SMALL)
        pdf.set_text_color(*CINZA_MEDIO)
        pdf.cell(box_w - 2, 6, label, align="C", fill=True)
        pdf.set_xy(x, pdf.get_y() + 6)
        pdf.set_font(FONT_BODY, "B", SIZE_BODY + 1)
        pdf.set_text_color(*TEXTO)
        pdf.cell(box_w - 2, 8, value, align="C", fill=True)

    pdf.set_xy(MARGIN_LEFT, pdf.get_y() + 14)

    # Análise IA da carteira
    pdf.set_text_color(*TEXTO)
    pdf.set_font(FONT_BODY, "", SIZE_BODY)
    _write_multiline(pdf, portfolio_ai)


def add_overview_table(pdf: FPDF, assets: list):
    """Adiciona tabela de visão geral dos ativos."""
    pdf.add_page()
    _section_header(pdf, "VISÃO GERAL DOS ATIVOS")

    # Cabeçalho da tabela
    pdf.set_font(FONT_BODY, "B", SIZE_SMALL)
    pdf.set_fill_color(*VERDE_ESCURO)
    pdf.set_text_color(*BRANCO)

    cols = [
        ("Ativo", 45), ("Tipo", 15), ("Saldo", 30),
        ("Aloc.%", 16), ("Mês%", 18), ("CDI M%", 18),
        ("Ano%", 18), ("CDI A%", 18),
    ]

    for label, w in cols:
        pdf.cell(w, 7, label, border=1, align="C", fill=True)
    pdf.ln()

    # Dados
    pdf.set_text_color(*TEXTO)
    pdf.set_font(FONT_BODY, "", SIZE_TINY)

    for i, asset in enumerate(assets):
        _check_page_space(pdf, 8)
        if i % 2 == 0:
            pdf.set_fill_color(*FUNDO_CLARO)
        else:
            pdf.set_fill_color(*BRANCO)

        fill = True
        nome_display = sanitize_text(asset.nome[:22] if len(asset.nome) > 22 else asset.nome)
        pdf.cell(45, 6, nome_display, border=1, fill=fill)
        pdf.cell(15, 6, asset.tipo[:5], border=1, align="C", fill=fill)
        pdf.cell(30, 6, format_brl(asset.saldo_bruto), border=1, align="R", fill=fill)
        pdf.cell(16, 6, f"{asset.alocacao:.1f}%", border=1, align="C", fill=fill)
        pdf.cell(18, 6, f"{asset.rent_mes:.2f}%", border=1, align="C", fill=fill)
        pdf.cell(18, 6, f"{asset.cdi_mes:.1f}%", border=1, align="C", fill=fill)
        pdf.cell(18, 6, f"{asset.rent_ano:.2f}%", border=1, align="C", fill=fill)
        pdf.cell(18, 6, f"{asset.cdi_ano:.1f}%", border=1, align="C", fill=fill)
        pdf.ln()


def add_consolidated_section(pdf: FPDF, portfolio_analysis: Dict, chart_paths: Dict):
    """Adiciona seção consolidada com gráficos."""
    pdf.add_page()
    _section_header(pdf, "ANÁLISE CONSOLIDADA")

    # Concentração
    pdf.set_font(FONT_BODY, "", SIZE_BODY)
    nivel = portfolio_analysis["nivel_concentração"]
    hhi = portfolio_analysis["concentração_hhi"]
    pdf.cell(CONTENT_WIDTH, 7,
             f"Nível de concentração: {nivel} (HHI: {hhi:.0f})",
             new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)

    # Gráficos
    for key, label in [("type_bars", ""), ("sector_pie", ""), ("return_mes", ""), ("return_ano", "")]:
        path = chart_paths.get(key)
        if path and path.exists():
            _check_page_space(pdf, 80)
            try:
                pdf.image(str(path), x=MARGIN_LEFT, w=CONTENT_WIDTH, h=65)
                pdf.ln(68)
            except Exception:
                pass


def add_sources_section(pdf: FPDF, sources: List[Dict]):
    """Adiciona seção com fontes de dados consultadas."""
    pdf.add_page()
    _section_header(pdf, "FONTES DE DADOS")

    pdf.set_font(FONT_BODY, "", SIZE_SMALL)
    pdf.cell(CONTENT_WIDTH, 7,
             f"Total de consultas realizadas: {len(sources)}",
             new_x="LMARGIN", new_y="NEXT")
    pdf.ln(3)

    # Tabela de fontes
    pdf.set_font(FONT_BODY, "B", SIZE_TINY)
    pdf.set_fill_color(*VERDE_ESCURO)
    pdf.set_text_color(*BRANCO)
    pdf.cell(25, 6, "Tipo", border=1, fill=True, align="C")
    pdf.cell(30, 6, "Fonte", border=1, fill=True, align="C")
    pdf.cell(30, 6, "Ticker", border=1, fill=True, align="C")
    pdf.cell(15, 6, "Status", border=1, fill=True, align="C")
    pdf.cell(CONTENT_WIDTH - 100, 6, "URL", border=1, fill=True, align="C")
    pdf.ln()

    pdf.set_text_color(*TEXTO)
    pdf.set_font(FONT_BODY, "", SIZE_TINY)

    for i, src in enumerate(sources[:50]):  # Limita a 50
        _check_page_space(pdf, 8)
        if i % 2 == 0:
            pdf.set_fill_color(*FUNDO_CLARO)
        else:
            pdf.set_fill_color(*BRANCO)
        fill = True
        url_display = src.get("url", "")[:45]
        pdf.cell(25, 5, src.get("tipo", ""), border=1, fill=fill)
        pdf.cell(30, 5, src.get("nome", ""), border=1, fill=fill)
        pdf.cell(30, 5, src.get("ticker", "")[:15], border=1, fill=fill)
        pdf.cell(15, 5, src.get("status", ""), border=1, align="C", fill=fill)
        pdf.cell(CONTENT_WIDTH - 100, 5, url_display, border=1, fill=fill)
        pdf.ln()


def add_disclaimer(pdf: FPDF):
    """Adiciona página de disclaimer."""
    pdf.add_page()
    _section_header(pdf, "DISCLAIMER")

    pdf.set_font(FONT_BODY, "", SIZE_SMALL)
    pdf.set_text_color(*TEXTO)

    disclaimer = (
        "Este relatório foi gerado automaticamente por um sistema de inteligência artificial "
        "e tem caráter exclusivamente informativo. As informações aqui contidas não constituem "
        "recomendação de investimento, oferta ou solicitação de compra ou venda de qualquer "
        "ativo financeiro.\n\n"
        "Os dados apresentados foram coletados de fontes públicas (brapi.dev, Banco Central do "
        "Brasil, Google News) e do relatório XP Performance do cliente. Embora tenhamos buscado "
        "precisão, não garantimos a completude ou exatidão das informações.\n\n"
        "Rentabilidade passada não é garantia de resultados futuros. Todo investimento envolve "
        "riscos, incluindo a possível perda do capital investido.\n\n"
        "As análises geradas por IA (Google Gemini) representam uma interpretação automatizada "
        "dos dados e não substituem a análise de um profissional qualificado.\n\n"
        "Consulte sempre seu assessor de investimentos antes de tomar qualquer decisão."
    )

    _write_multiline(pdf, disclaimer)

    pdf.ln(10)
    pdf.set_font(FONT_BODY, "I", SIZE_TINY)
    pdf.set_text_color(*CINZA_MEDIO)
    pdf.cell(CONTENT_WIDTH, 5, "Somus Capital - Assessoria de Investimentos",
             new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.cell(CONTENT_WIDTH, 5, "Documento gerado automaticamente - Agente de Investimentos",
             new_x="LMARGIN", new_y="NEXT", align="C")


def _write_multiline(pdf: FPDF, text: str):
    """Escreve texto multi-linha com quebra automática, tratando markdown básico."""
    text = sanitize_text(text)
    pdf.set_font(FONT_BODY, "", SIZE_BODY)
    for line in text.split("\n"):
        line = line.strip()
        if not line:
            pdf.ln(4)
            continue

        # Detecta títulos com ** ou ##
        if line.startswith("**") and line.endswith("**"):
            pdf.set_font(FONT_BODY, "B", SIZE_BODY)
            pdf.multi_cell(CONTENT_WIDTH, 6, line.replace("**", ""))
            pdf.set_font(FONT_BODY, "", SIZE_BODY)
        elif line.startswith("## ") or line.startswith("# "):
            pdf.set_font(FONT_BODY, "B", SIZE_BODY + 1)
            pdf.multi_cell(CONTENT_WIDTH, 6, line.lstrip("#").strip())
            pdf.set_font(FONT_BODY, "", SIZE_BODY)
        elif line.startswith("- ") or line.startswith("* "):
            bullet_text = line[2:]
            # Handle bold within bullets
            if "**" in bullet_text:
                parts = bullet_text.split("**")
                pdf.cell(5, 5, "-")  # bullet char
                for j, part in enumerate(parts):
                    if j % 2 == 1:
                        pdf.set_font(FONT_BODY, "B", SIZE_BODY)
                    else:
                        pdf.set_font(FONT_BODY, "", SIZE_BODY)
                    pdf.write(5, part)
                pdf.ln()
            else:
                pdf.cell(5, 5, "-")
                pdf.multi_cell(CONTENT_WIDTH - 5, 5, f" {bullet_text}")
        else:
            # Remove markdown bold inline
            clean = line.replace("**", "")
            pdf.multi_cell(CONTENT_WIDTH, 5, clean)
