"""Gerador de PDF consolidado multi-instituicao -Somus Capital."""

from pathlib import Path

from agente_investimentos.consolidador.models import ConsolidatedPortfolio
from agente_investimentos.report.base_pdf import SomusPDF, _data_completa, check_space, section_bar
from agente_investimentos.report.styles import (
    VERDE_ESCURO, AZUL, BRANCO, TEXTO, FUNDO_CLARO, CINZA_MEDIO, VERDE_CLARO,
    FONT_TITLE, FONT_BODY,
    SIZE_TITLE, SIZE_SUBTITLE, SIZE_SECTION, SIZE_BODY, SIZE_SMALL, SIZE_TINY,
    MARGIN_LEFT, MARGIN_RIGHT, CONTENT_WIDTH, CHART_PALETTE,
)
from agente_investimentos.config import PASTA_SAIDA, LOGO_PATH
from agente_investimentos.utils.formatters import sanitize_text


def _fmt_brl(value: float) -> str:
    """Formata valor em BRL."""
    if value >= 1_000_000:
        return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _fmt_pct(value: float) -> str:
    """Formata percentual."""
    return f"{value:+.2f}%"


def _color_for_value(value: float):
    """Retorna cor verde/vermelho baseado no valor."""
    if value > 0:
        return VERDE_ESCURO
    elif value < 0:
        return (198, 40, 40)  # vermelho
    return TEXTO


class ConsolidadorPDFBuilder:
    """Gera relatorio PDF consolidado de multiplas instituicoes."""

    def __init__(self, portfolio: ConsolidatedPortfolio):
        self.cp = portfolio

    def build(self) -> Path:
        """Constroi o PDF e retorna o caminho."""
        logo = str(LOGO_PATH) if LOGO_PATH.exists() else None
        pdf = SomusPDF(logo_path=logo)
        pdf.set_auto_page_break(auto=True, margin=20)
        pdf.set_margins(MARGIN_LEFT, 15, MARGIN_RIGHT)

        self._add_cover(pdf)
        self._add_visao_geral(pdf)
        self._add_comparativo_instituicoes(pdf)
        self._add_distribuicao_por_tipo(pdf)
        self._add_ranking_risco(pdf)
        self._add_ranking_rentabilidade(pdf)
        self._add_detalhamento_por_instituicao(pdf)
        self._add_todos_ativos(pdf)
        self._add_conclusao(pdf)

        output_path = PASTA_SAIDA / "Relatorio_Consolidado.pdf"
        pdf.output(str(output_path))
        return output_path

    def _add_cover(self, pdf):
        """Capa do relatorio."""
        pdf.add_page()
        pdf.skip_footer_on_current_page()

        # Fundo verde escuro
        pdf.set_fill_color(*VERDE_ESCURO)
        pdf.rect(0, 0, 210, 297, "F")

        # Logo
        if LOGO_PATH.exists():
            try:
                pdf.image(str(LOGO_PATH), x=70, y=40, w=70)
            except Exception:
                pass

        # Titulo
        pdf.set_y(95)
        pdf.set_font(FONT_TITLE, "B", 28)
        pdf.set_text_color(*BRANCO)
        pdf.cell(CONTENT_WIDTH, 14, "RELATORIO CONSOLIDADO", align="C", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(4)
        pdf.set_font(FONT_BODY, "", 14)
        pdf.cell(CONTENT_WIDTH, 8, "Carteira Multi-Instituicao", align="C", new_x="LMARGIN", new_y="NEXT")

        # Linha decorativa
        pdf.ln(10)
        pdf.set_draw_color(*BRANCO)
        pdf.set_line_width(0.5)
        x_center = 105
        pdf.line(x_center - 30, pdf.get_y(), x_center + 30, pdf.get_y())

        # Info
        pdf.ln(10)
        pdf.set_font(FONT_BODY, "", 11)
        pdf.set_text_color(200, 220, 210)
        pdf.cell(CONTENT_WIDTH, 7, f"{self.cp.num_instituicoes} Instituicoes | {self.cp.num_ativos_total} Ativos", align="C", new_x="LMARGIN", new_y="NEXT")
        pdf.cell(CONTENT_WIDTH, 7, f"Patrimonio Total: {_fmt_brl(self.cp.patrimonio_bruto_total)}", align="C", new_x="LMARGIN", new_y="NEXT")

        # Instituicoes listadas
        pdf.ln(8)
        pdf.set_font(FONT_BODY, "", 10)
        for inst in self.cp.instituicoes:
            pdf.cell(CONTENT_WIDTH, 6, f"{inst.nome} -{_fmt_brl(inst.patrimonio_bruto)}", align="C", new_x="LMARGIN", new_y="NEXT")

        # Data
        pdf.set_y(250)
        pdf.set_font(FONT_BODY, "", 9)
        pdf.set_text_color(180, 200, 190)
        pdf.cell(CONTENT_WIDTH, 6, f"Gerado em {_data_completa()}", align="C", new_x="LMARGIN", new_y="NEXT")
        pdf.cell(CONTENT_WIDTH, 6, "Somus Capital -Investment HUB", align="C", new_x="LMARGIN", new_y="NEXT")

    def _add_visao_geral(self, pdf):
        """Pagina de visao geral consolidada."""
        pdf.add_page()
        pdf.set_text_color(*TEXTO)
        section_bar(pdf, "VISAO GERAL CONSOLIDADA")
        pdf.ln(2)

        # KPIs em grid
        kpis = [
            ("Patrimonio Bruto Total", _fmt_brl(self.cp.patrimonio_bruto_total)),
            ("Patrimonio Liquido Total", _fmt_brl(self.cp.patrimonio_liquido_total)),
            ("Impostos Totais", _fmt_brl(self.cp.impostos_totais)),
            ("Numero de Ativos", str(self.cp.num_ativos_total)),
            ("Numero de Instituicoes", str(self.cp.num_instituicoes)),
            ("Rent. Mes (ponderada)", _fmt_pct(self.cp.rent_mes_ponderada())),
            ("Rent. Ano (ponderada)", _fmt_pct(self.cp.rent_ano_ponderada())),
        ]

        col_w = CONTENT_WIDTH / 2
        for i, (label, value) in enumerate(kpis):
            x = MARGIN_LEFT + (i % 2) * col_w
            if i % 2 == 0 and i > 0:
                pdf.ln(1)
            check_space(pdf, 14)

            pdf.set_x(x)
            pdf.set_font(FONT_BODY, "", SIZE_TINY)
            pdf.set_text_color(*CINZA_MEDIO)
            pdf.cell(col_w, 4, sanitize_text(label), new_x="LEFT", new_y="NEXT")
            pdf.set_x(x)
            pdf.set_font(FONT_BODY, "B", SIZE_BODY)
            pdf.set_text_color(*TEXTO)
            pdf.cell(col_w, 5, sanitize_text(value), new_x="LMARGIN", new_y="NEXT" if i % 2 == 1 else "TOP")

        pdf.ln(6)

        # CDI info do Safra (se disponivel)
        for inst in self.cp.instituicoes:
            if inst.cdi_ano > 0:
                check_space(pdf, 10)
                pdf.set_font(FONT_BODY, "", SIZE_SMALL)
                pdf.set_text_color(*TEXTO)
                pdf.cell(CONTENT_WIDTH, 5, sanitize_text(
                    f"CDI Equivalente ({inst.nome}): Mes {inst.cdi_mes:.1f}% | Ano {inst.cdi_ano:.1f}%"
                ), new_x="LMARGIN", new_y="NEXT")

        pdf.ln(3)

        # Perfis de investidor
        check_space(pdf, 20)
        section_bar(pdf, "PERFIS DE INVESTIDOR", color=AZUL)
        pdf.ln(2)
        for inst in self.cp.instituicoes:
            if inst.perfil_investidor:
                pdf.set_font(FONT_BODY, "", SIZE_SMALL)
                pdf.cell(CONTENT_WIDTH, 5, sanitize_text(
                    f"{inst.nome}: Perfil {inst.perfil_investidor}"
                ), new_x="LMARGIN", new_y="NEXT")

    def _add_comparativo_instituicoes(self, pdf):
        """Tabela comparativa entre instituicoes."""
        pdf.add_page()
        section_bar(pdf, "COMPARATIVO POR INSTITUICAO")
        pdf.ln(3)

        dist = self.cp.distribuicao_por_instituicao()

        # Header da tabela
        cols = [
            ("Instituicao", 35),
            ("Patrimonio Bruto", 35),
            ("Ativos", 15),
            ("Alocacao", 20),
            ("Rent. Mes", 22),
            ("Rent. Ano", 22),
            ("Rent. 12m", 22),
        ]
        total_w = sum(c[1] for c in cols)
        scale = CONTENT_WIDTH / total_w
        cols = [(n, w * scale) for n, w in cols]

        # Header
        pdf.set_fill_color(*VERDE_ESCURO)
        pdf.set_text_color(*BRANCO)
        pdf.set_font(FONT_BODY, "B", SIZE_TINY)
        for name, w in cols:
            pdf.cell(w, 6, sanitize_text(name), border=1, align="C", fill=True)
        pdf.ln()

        # Linhas
        pdf.set_text_color(*TEXTO)
        pdf.set_font(FONT_BODY, "", SIZE_TINY)
        for inst_nome, d in dist.items():
            bg = FUNDO_CLARO if list(dist.keys()).index(inst_nome) % 2 == 0 else BRANCO
            pdf.set_fill_color(*bg)
            pdf.cell(cols[0][1], 5.5, sanitize_text(inst_nome), border=1, fill=True)
            pdf.cell(cols[1][1], 5.5, _fmt_brl(d["patrimonio_bruto"]), border=1, align="R", fill=True)
            pdf.cell(cols[2][1], 5.5, str(d["num_ativos"]), border=1, align="C", fill=True)
            pdf.cell(cols[3][1], 5.5, f"{d['alocacao']:.1f}%", border=1, align="C", fill=True)
            pdf.cell(cols[4][1], 5.5, _fmt_pct(d["rent_mes"]), border=1, align="C", fill=True)
            pdf.cell(cols[5][1], 5.5, _fmt_pct(d["rent_ano"]), border=1, align="C", fill=True)
            pdf.cell(cols[6][1], 5.5, _fmt_pct(d.get("rent_12m", 0)), border=1, align="C", fill=True)
            pdf.ln()

        # Total
        pdf.set_fill_color(*VERDE_ESCURO)
        pdf.set_text_color(*BRANCO)
        pdf.set_font(FONT_BODY, "B", SIZE_TINY)
        pdf.cell(cols[0][1], 5.5, "TOTAL", border=1, fill=True)
        pdf.cell(cols[1][1], 5.5, _fmt_brl(self.cp.patrimonio_bruto_total), border=1, align="R", fill=True)
        pdf.cell(cols[2][1], 5.5, str(self.cp.num_ativos_total), border=1, align="C", fill=True)
        pdf.cell(cols[3][1], 5.5, "100%", border=1, align="C", fill=True)
        pdf.cell(cols[4][1], 5.5, _fmt_pct(self.cp.rent_mes_ponderada()), border=1, align="C", fill=True)
        pdf.cell(cols[5][1], 5.5, _fmt_pct(self.cp.rent_ano_ponderada()), border=1, align="C", fill=True)
        pdf.cell(cols[6][1], 5.5, "", border=1, align="C", fill=True)
        pdf.ln()
        pdf.set_text_color(*TEXTO)

    def _add_distribuicao_por_tipo(self, pdf):
        """Distribuicao por tipo de ativo consolidado."""
        pdf.ln(8)
        check_space(pdf, 50)
        section_bar(pdf, "DISTRIBUICAO POR TIPO DE ATIVO (CONSOLIDADO)")
        pdf.ln(3)

        dist = self.cp.distribuicao_por_tipo()

        # Header
        cols = [("Tipo", 40), ("Qtd", 15), ("Saldo Bruto", 40), ("Alocacao", 25), ("Barra", 60)]
        total_w = sum(c[1] for c in cols)
        scale = CONTENT_WIDTH / total_w
        cols = [(n, w * scale) for n, w in cols]

        pdf.set_fill_color(*VERDE_ESCURO)
        pdf.set_text_color(*BRANCO)
        pdf.set_font(FONT_BODY, "B", SIZE_TINY)
        for name, w in cols:
            pdf.cell(w, 6, sanitize_text(name), border=1, align="C", fill=True)
        pdf.ln()

        pdf.set_text_color(*TEXTO)
        pdf.set_font(FONT_BODY, "", SIZE_TINY)
        color_idx = 0
        for tipo, d in dist.items():
            check_space(pdf, 7)
            bg = FUNDO_CLARO if color_idx % 2 == 0 else BRANCO
            pdf.set_fill_color(*bg)
            pdf.cell(cols[0][1], 5.5, sanitize_text(tipo), border=1, fill=True)
            pdf.cell(cols[1][1], 5.5, str(d["count"]), border=1, align="C", fill=True)
            pdf.cell(cols[2][1], 5.5, _fmt_brl(d["saldo_bruto"]), border=1, align="R", fill=True)
            pdf.cell(cols[3][1], 5.5, f"{d['alocacao']:.1f}%", border=1, align="C", fill=True)

            # Barra visual
            bar_x = pdf.get_x() + 1
            bar_y = pdf.get_y() + 1
            bar_max = cols[4][1] - 2
            bar_w = max(1, d['alocacao'] / 100 * bar_max)
            pdf.cell(cols[4][1], 5.5, "", border=1, fill=True)
            # Pinta barra
            hex_color = CHART_PALETTE[color_idx % len(CHART_PALETTE)]
            r = int(hex_color[1:3], 16)
            g = int(hex_color[3:5], 16)
            b = int(hex_color[5:7], 16)
            pdf.set_fill_color(r, g, b)
            pdf.rect(bar_x, bar_y, bar_w, 3.5, "F")

            pdf.ln()
            color_idx += 1

    def _add_ranking_risco(self, pdf):
        """Ranking de risco por instituicao."""
        pdf.ln(8)
        check_space(pdf, 40)
        section_bar(pdf, "ANALISE DE RISCO POR INSTITUICAO", color=(198, 40, 40))
        pdf.ln(3)

        ranking = self.cp.ranking_risco_por_instituicao()

        pdf.set_font(FONT_BODY, "", SIZE_SMALL)
        pdf.set_text_color(*TEXTO)
        pdf.multi_cell(CONTENT_WIDTH, 4.5, sanitize_text(
            "Ativos de risco incluem: Acoes, Multimercado, Op. Estruturadas, Opcoes e Futuros."
        ))
        pdf.ln(3)

        cols = [("Instituicao", 40), ("Ativos Risco", 25), ("Saldo Risco", 35), ("% Risco", 25), ("Ativos Total", 25)]
        total_w = sum(c[1] for c in cols)
        scale = CONTENT_WIDTH / total_w
        cols = [(n, w * scale) for n, w in cols]

        pdf.set_fill_color(198, 40, 40)
        pdf.set_text_color(*BRANCO)
        pdf.set_font(FONT_BODY, "B", SIZE_TINY)
        for name, w in cols:
            pdf.cell(w, 6, sanitize_text(name), border=1, align="C", fill=True)
        pdf.ln()

        pdf.set_text_color(*TEXTO)
        pdf.set_font(FONT_BODY, "", SIZE_TINY)
        for i, r in enumerate(ranking):
            bg = FUNDO_CLARO if i % 2 == 0 else BRANCO
            pdf.set_fill_color(*bg)
            pdf.cell(cols[0][1], 5.5, sanitize_text(r["instituicao"]), border=1, fill=True)
            pdf.cell(cols[1][1], 5.5, str(r["ativos_risco"]), border=1, align="C", fill=True)
            pdf.cell(cols[2][1], 5.5, _fmt_brl(r["saldo_risco"]), border=1, align="R", fill=True)
            pdf.cell(cols[3][1], 5.5, f"{r['pct_risco']:.1f}%", border=1, align="C", fill=True)
            pdf.cell(cols[4][1], 5.5, str(r["ativos_total"]), border=1, align="C", fill=True)
            pdf.ln()

    def _add_ranking_rentabilidade(self, pdf):
        """Top melhores e piores rentabilidades."""
        pdf.add_page()
        section_bar(pdf, "MELHORES RENTABILIDADES NO ANO")
        pdf.ln(3)

        self._render_ranking_table(pdf, self.cp.melhores_rentabilidades(), VERDE_ESCURO)

        pdf.ln(8)
        check_space(pdf, 50)
        section_bar(pdf, "PIORES RENTABILIDADES NO ANO", color=(198, 40, 40))
        pdf.ln(3)

        self._render_ranking_table(pdf, self.cp.piores_rentabilidades(), (198, 40, 40))

    def _render_ranking_table(self, pdf, items: list, header_color):
        """Renderiza tabela de ranking."""
        cols = [("Ativo", 45), ("Tipo", 25), ("Instituicao", 25), ("Saldo", 30), ("Rent.Mes", 22), ("Rent.Ano", 22)]
        total_w = sum(c[1] for c in cols)
        scale = CONTENT_WIDTH / total_w
        cols = [(n, w * scale) for n, w in cols]

        pdf.set_fill_color(*header_color)
        pdf.set_text_color(*BRANCO)
        pdf.set_font(FONT_BODY, "B", SIZE_TINY)
        for name, w in cols:
            pdf.cell(w, 6, sanitize_text(name), border=1, align="C", fill=True)
        pdf.ln()

        pdf.set_font(FONT_BODY, "", SIZE_TINY)
        for i, item in enumerate(items):
            check_space(pdf, 7)
            bg = FUNDO_CLARO if i % 2 == 0 else BRANCO
            pdf.set_fill_color(*bg)
            nome = item.get("ticker") or item.get("nome", "")
            if len(nome) > 25:
                nome = nome[:23] + ".."
            pdf.set_text_color(*TEXTO)
            pdf.cell(cols[0][1], 5.5, sanitize_text(nome), border=1, fill=True)
            pdf.cell(cols[1][1], 5.5, sanitize_text(item.get("tipo", "")), border=1, align="C", fill=True)
            pdf.cell(cols[2][1], 5.5, sanitize_text(item.get("instituicao", "")), border=1, align="C", fill=True)
            pdf.cell(cols[3][1], 5.5, _fmt_brl(item.get("saldo_bruto", 0)), border=1, align="R", fill=True)

            # Rent mes com cor
            rm = item.get("rent_mes", 0)
            pdf.set_text_color(*_color_for_value(rm))
            pdf.cell(cols[4][1], 5.5, _fmt_pct(rm), border=1, align="C", fill=True)

            # Rent ano com cor
            ra = item.get("rent_ano", 0)
            pdf.set_text_color(*_color_for_value(ra))
            pdf.cell(cols[5][1], 5.5, _fmt_pct(ra), border=1, align="C", fill=True)

            pdf.set_text_color(*TEXTO)
            pdf.ln()

    def _add_detalhamento_por_instituicao(self, pdf):
        """Detalhamento por instituicao."""
        for inst in self.cp.instituicoes:
            pdf.add_page()
            section_bar(pdf, f"DETALHAMENTO -{sanitize_text(inst.nome.upper())}", color=AZUL)
            pdf.ln(3)

            # Info geral
            pdf.set_font(FONT_BODY, "", SIZE_SMALL)
            info_lines = [
                f"Conta: {inst.conta}",
                f"Data de referencia: {inst.data_referencia}",
                f"Patrimonio Bruto: {_fmt_brl(inst.patrimonio_bruto)}",
                f"Patrimonio Liquido: {_fmt_brl(inst.patrimonio_liquido)}",
                f"Impostos Previstos: {_fmt_brl(inst.impostos_totais)}",
                f"Numero de Ativos: {inst.num_ativos}",
            ]
            if inst.rent_carteira_mes:
                info_lines.append(f"Rentabilidade Mes: {_fmt_pct(inst.rent_carteira_mes)}")
            if inst.rent_carteira_ano:
                info_lines.append(f"Rentabilidade Ano: {_fmt_pct(inst.rent_carteira_ano)}")
            if inst.rent_carteira_12m:
                info_lines.append(f"Rentabilidade 12M: {_fmt_pct(inst.rent_carteira_12m)}")
            if inst.cdi_mes:
                info_lines.append(f"CDI Equivalente Mes: {inst.cdi_mes:.1f}%")
            if inst.perfil_investidor:
                info_lines.append(f"Perfil: {inst.perfil_investidor}")

            for line in info_lines:
                pdf.cell(CONTENT_WIDTH, 4.5, sanitize_text(line), new_x="LMARGIN", new_y="NEXT")

            pdf.ln(5)

            # Tabela de ativos
            if not inst.ativos:
                pdf.set_font(FONT_BODY, "I", SIZE_SMALL)
                pdf.cell(CONTENT_WIDTH, 5, "Nenhum ativo detalhado disponivel.", new_x="LMARGIN", new_y="NEXT")
                continue

            cols = [("Ativo", 50), ("Tipo", 22), ("Saldo Bruto", 28), ("%PL", 15), ("Mes", 18), ("Ano", 18), ("12m", 18)]
            total_w = sum(c[1] for c in cols)
            scale = CONTENT_WIDTH / total_w
            cols = [(n, w * scale) for n, w in cols]

            pdf.set_fill_color(*AZUL)
            pdf.set_text_color(*BRANCO)
            pdf.set_font(FONT_BODY, "B", SIZE_TINY)
            for name, w in cols:
                pdf.cell(w, 6, sanitize_text(name), border=1, align="C", fill=True)
            pdf.ln()

            pdf.set_font(FONT_BODY, "", SIZE_TINY)
            for i, a in enumerate(inst.ativos):
                check_space(pdf, 7)
                bg = FUNDO_CLARO if i % 2 == 0 else BRANCO
                pdf.set_fill_color(*bg)
                nome = a.ticker if a.ticker else a.nome
                if len(nome) > 28:
                    nome = nome[:26] + ".."
                pdf.set_text_color(*TEXTO)
                pdf.cell(cols[0][1], 5.5, sanitize_text(nome), border=1, fill=True)
                pdf.cell(cols[1][1], 5.5, sanitize_text(a.tipo[:12]), border=1, align="C", fill=True)
                pdf.cell(cols[2][1], 5.5, _fmt_brl(a.saldo_bruto), border=1, align="R", fill=True)
                pdf.cell(cols[3][1], 5.5, f"{a.alocacao_pct:.1f}%", border=1, align="C", fill=True)

                rm = a.rent_mes
                pdf.set_text_color(*_color_for_value(rm))
                pdf.cell(cols[4][1], 5.5, _fmt_pct(rm) if rm else "-", border=1, align="C", fill=True)

                ra = a.rent_ano
                pdf.set_text_color(*_color_for_value(ra))
                pdf.cell(cols[5][1], 5.5, _fmt_pct(ra) if ra else "-", border=1, align="C", fill=True)

                r12 = a.rent_12m
                pdf.set_text_color(*_color_for_value(r12))
                pdf.cell(cols[6][1], 5.5, _fmt_pct(r12) if r12 else "-", border=1, align="C", fill=True)

                pdf.set_text_color(*TEXTO)
                pdf.ln()

    def _add_todos_ativos(self, pdf):
        """Lista completa de todos os ativos consolidados."""
        pdf.add_page()
        section_bar(pdf, "TODOS OS ATIVOS -VISAO CONSOLIDADA")
        pdf.ln(3)

        all_ativos = sorted(self.cp.todos_ativos, key=lambda a: a.saldo_bruto, reverse=True)

        cols = [("Ativo", 42), ("Inst.", 18), ("Tipo", 20), ("Saldo", 28), ("%Total", 15), ("Mes", 16), ("Ano", 16), ("12m", 16)]
        total_w = sum(c[1] for c in cols)
        scale = CONTENT_WIDTH / total_w
        cols = [(n, w * scale) for n, w in cols]

        pdf.set_fill_color(*VERDE_ESCURO)
        pdf.set_text_color(*BRANCO)
        pdf.set_font(FONT_BODY, "B", SIZE_TINY)
        for name, w in cols:
            pdf.cell(w, 6, sanitize_text(name), border=1, align="C", fill=True)
        pdf.ln()

        total_bruto = self.cp.patrimonio_bruto_total
        pdf.set_font(FONT_BODY, "", SIZE_TINY)
        for i, a in enumerate(all_ativos):
            check_space(pdf, 7)
            bg = FUNDO_CLARO if i % 2 == 0 else BRANCO
            pdf.set_fill_color(*bg)
            nome = a.ticker if a.ticker else a.nome
            if len(nome) > 24:
                nome = nome[:22] + ".."
            pct_total = (a.saldo_bruto / total_bruto * 100) if total_bruto else 0

            pdf.set_text_color(*TEXTO)
            pdf.cell(cols[0][1], 5, sanitize_text(nome), border=1, fill=True)
            pdf.cell(cols[1][1], 5, sanitize_text(a.instituicao[:10]), border=1, align="C", fill=True)
            pdf.cell(cols[2][1], 5, sanitize_text(a.tipo[:10]), border=1, align="C", fill=True)
            pdf.cell(cols[3][1], 5, _fmt_brl(a.saldo_bruto), border=1, align="R", fill=True)
            pdf.cell(cols[4][1], 5, f"{pct_total:.1f}%", border=1, align="C", fill=True)

            for val, col_idx in [(a.rent_mes, 5), (a.rent_ano, 6), (a.rent_12m, 7)]:
                pdf.set_text_color(*_color_for_value(val))
                pdf.cell(cols[col_idx][1], 5, _fmt_pct(val) if val else "-", border=1, align="C", fill=True)

            pdf.set_text_color(*TEXTO)
            pdf.ln()

    def _add_conclusao(self, pdf):
        """Pagina de conclusao/estrategia."""
        pdf.add_page()
        section_bar(pdf, "ESTRATEGIA E DISTRIBUICAO CONSOLIDADA")
        pdf.ln(4)

        pdf.set_font(FONT_BODY, "", SIZE_SMALL)
        pdf.set_text_color(*TEXTO)

        # Resumo estrategico
        dist_tipo = self.cp.distribuicao_por_tipo()
        dist_inst = self.cp.distribuicao_por_instituicao()
        total = self.cp.patrimonio_bruto_total

        lines = [
            f"O patrimonio consolidado totaliza {_fmt_brl(total)}, distribuido em {self.cp.num_instituicoes} instituicoes "
            f"e {self.cp.num_ativos_total} ativos.",
            "",
        ]

        # Concentracao
        if dist_inst:
            maior_inst = max(dist_inst.items(), key=lambda x: x[1]["patrimonio_bruto"])
            lines.append(
                f"A maior concentracao esta em {maior_inst[0]}, representando "
                f"{maior_inst[1]['alocacao']:.1f}% do patrimonio total."
            )
            lines.append("")

        # Tipo dominante
        if dist_tipo:
            maior_tipo = list(dist_tipo.items())[0]
            lines.append(
                f"O tipo de ativo dominante e {maior_tipo[0]}, com {maior_tipo[1]['count']} ativos "
                f"e {maior_tipo[1]['alocacao']:.1f}% da alocacao total."
            )
            lines.append("")

        # CDI info
        for inst in self.cp.instituicoes:
            if inst.cdi_ano > 0:
                lines.append(
                    f"A carteira {inst.nome} rendeu {inst.cdi_ano:.1f}% do CDI no ano, "
                    f"com rentabilidade de {_fmt_pct(inst.rent_carteira_ano)} acumulada."
                )

        lines.append("")

        # Risco
        ranking = self.cp.ranking_risco_por_instituicao()
        total_risco = sum(r["saldo_risco"] for r in ranking)
        pct_risco = (total_risco / total * 100) if total else 0
        lines.append(
            f"Do total consolidado, {_fmt_brl(total_risco)} ({pct_risco:.1f}%) esta alocado em ativos de maior risco "
            f"(acoes, multimercado, operacoes estruturadas)."
        )
        lines.append("")

        # Piores
        piores = self.cp.piores_rentabilidades()
        if piores and piores[0]["rent_ano"] < 0:
            lines.append(
                f"Destaque negativo: {piores[0]['nome']} ({piores[0]['instituicao']}) "
                f"com {_fmt_pct(piores[0]['rent_ano'])} no ano -merece atencao do assessor."
            )

        for line in lines:
            check_space(pdf, 6)
            pdf.multi_cell(CONTENT_WIDTH, 4.5, sanitize_text(line))

        pdf.ln(6)

        # Distribuicao visual final
        check_space(pdf, 30)
        section_bar(pdf, "COMPOSICAO FINAL POR TIPO", color=AZUL)
        pdf.ln(3)

        for tipo, d in dist_tipo.items():
            check_space(pdf, 8)
            pdf.set_font(FONT_BODY, "B", SIZE_TINY)
            label = f"{sanitize_text(tipo)}: {d['alocacao']:.1f}% ({_fmt_brl(d['saldo_bruto'])})"
            pdf.cell(80, 4, label, new_x="LEFT", new_y="NEXT")

            # Barra visual
            bar_x = MARGIN_LEFT
            bar_y = pdf.get_y()
            bar_w = max(2, d['alocacao'] / 100 * CONTENT_WIDTH)
            pdf.set_fill_color(*VERDE_ESCURO)
            pdf.rect(bar_x, bar_y, bar_w, 3, "F")
            pdf.ln(5)

        # Disclaimer
        pdf.ln(8)
        check_space(pdf, 15)
        pdf.set_font(FONT_BODY, "I", SIZE_TINY)
        pdf.set_text_color(*CINZA_MEDIO)
        pdf.multi_cell(CONTENT_WIDTH, 3.5, sanitize_text(
            "Este relatorio e meramente informativo e nao constitui recomendacao de investimento. "
            "Rentabilidade passada nao garante rentabilidade futura. Consulte seu assessor de investimentos. "
            "Gerado automaticamente pelo Investment HUB -Somus Capital."
        ))
