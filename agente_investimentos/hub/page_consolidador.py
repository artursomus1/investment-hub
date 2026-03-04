"""Pagina Consolidador - consolida carteiras de multiplas instituicoes."""

import tempfile
from pathlib import Path

import streamlit as st

from agente_investimentos.hub.components import (
    render_hero_header, render_footer, format_brl, is_mobile,
)
from agente_investimentos.consolidador.models import ConsolidatedPortfolio


# Formatos aceitos e seus parsers
_SUPPORTED_FORMATS = {
    ".pdf": "XP, Safra, Itau ou outro (PDF)",
    ".xlsx": "BTG Pactual (XLSX)",
    ".xls": "BTG Pactual (XLS)",
}


def _detect_and_parse(file_path: str, filename: str):
    """Detecta instituicao e parseia o arquivo."""
    ext = Path(filename).suffix.lower()
    name_lower = filename.lower()

    if ext == ".pdf":
        import pdfplumber
        import warnings
        warnings.filterwarnings("ignore")
        with pdfplumber.open(file_path) as pdf:
            # Concatena texto das primeiras 3 paginas para deteccao
            pages_text = ""
            for p in pdf.pages[:3]:
                pages_text += (p.extract_text() or "") + "\n"
            pages_lower = pages_text.lower()

            # Detecta XP pelo conteudo (Posicao Consolidada + conta + assessor)
            if ("xp investimentos" in pages_lower or "assessor" in pages_lower
                    or "posicao detalhada" in pages_lower.replace("\xe7", "c").replace("\xe3", "a")
                    or "patrimonio investimento" in pages_lower.replace("\xf4", "o").replace("\xea", "e")):
                from agente_investimentos.consolidador.xp_parser import parse_xp_pdf
                return parse_xp_pdf(file_path)

            # Detecta Itau pelo conteudo
            if "itau" in pages_lower or "personnalite" in pages_lower or "total investido" in pages_lower:
                from agente_investimentos.consolidador.itau_parser import parse_itau_pdf
                return parse_itau_pdf(file_path)

            # Detecta Safra pelo conteudo
            if "safra" in pages_lower or "safrabm" in pages_lower:
                from agente_investimentos.consolidador.safra_parser import parse_safra_pdf
                return parse_safra_pdf(file_path)

        # Fallback: tenta parser Safra mesmo assim (formato similar)
        from agente_investimentos.consolidador.safra_parser import parse_safra_pdf
        return parse_safra_pdf(file_path)

    elif ext in (".xlsx", ".xls"):
        # Detecta BTG
        from agente_investimentos.consolidador.btg_parser import parse_btg_xlsx
        return parse_btg_xlsx(file_path)

    return None


def render():
    """Renderiza a pagina do consolidador."""
    mobile = is_mobile()

    render_hero_header(
        "Consolidador" if mobile else "Consolidador de Carteiras",
        "" if mobile else "Consolide relatorios de multiplas instituicoes em uma visao unica",
    )

    st.markdown(
        "Arraste seus relatorios abaixo. **Formatos aceitos**: PDF (XP, Safra, Itau) e XLSX (BTG Pactual)."
    )

    # Upload de arquivos
    uploaded_files = st.file_uploader(
        "Envie seus relatorios",
        type=["pdf", "xlsx", "xls"],
        accept_multiple_files=True,
        help="Aceita PDF (XP, Safra, Itau) e XLSX (BTG). Envie quantos quiser.",
    )

    if not uploaded_files:
        st.info("Envie pelo menos um relatorio para comecar a consolidacao.")
        render_footer()
        return

    # Mostra arquivos enviados
    st.markdown(f"**{len(uploaded_files)} arquivo(s) enviado(s):**")
    for f in uploaded_files:
        ext = Path(f.name).suffix.lower()
        icon = "📄" if ext == ".pdf" else "📊"
        st.caption(f"{icon} {f.name} ({f.size / 1024:.0f} KB)")

    # Botao de consolidacao
    run = st.button(
        "Consolidar e Gerar PDF",
        type="primary",
        use_container_width=True,
    )

    if run:
        instituicoes = []
        errors = []

        with st.spinner("Processando relatorios..."):
            for uploaded_file in uploaded_files:
                try:
                    # Salva em temp para parsing
                    suffix = Path(uploaded_file.name).suffix
                    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                        tmp.write(uploaded_file.read())
                        tmp_path = tmp.name

                    result = _detect_and_parse(tmp_path, uploaded_file.name)
                    if result and result.patrimonio_bruto > 0:
                        instituicoes.append(result)
                        st.success(f"{result.nome}: {result.num_ativos} ativos, {format_brl(result.patrimonio_bruto)}")
                    elif result:
                        st.warning(f"{uploaded_file.name}: Arquivo parseado mas sem patrimonio detectado.")
                    else:
                        errors.append(f"{uploaded_file.name}: Formato nao reconhecido.")
                except Exception as e:
                    errors.append(f"{uploaded_file.name}: Erro - {str(e)[:100]}")

                # Cleanup
                try:
                    Path(tmp_path).unlink()
                except Exception:
                    pass

        for err in errors:
            st.error(err)

        if not instituicoes:
            st.error("Nenhuma instituicao valida encontrada nos arquivos.")
            render_footer()
            return

        # Consolida
        cp = ConsolidatedPortfolio(instituicoes=instituicoes)
        st.session_state["consolidated_portfolio"] = cp

        # Gera PDF
        with st.spinner("Gerando relatorio PDF consolidado..."):
            from agente_investimentos.consolidador.pdf_builder import ConsolidadorPDFBuilder
            builder = ConsolidadorPDFBuilder(cp)
            pdf_path = builder.build()
            st.session_state["consolidated_pdf_path"] = str(pdf_path)

    # Renderiza resultados
    cp = st.session_state.get("consolidated_portfolio")
    pdf_path = st.session_state.get("consolidated_pdf_path")

    if cp:
        st.divider()

        # KPIs
        if mobile:
            r1, r2 = st.columns(2)
            r1.metric("Patrimonio Total", format_brl(cp.patrimonio_bruto_total))
            r2.metric("Instituicoes", cp.num_instituicoes)
            r3, r4 = st.columns(2)
            r3.metric("Ativos", cp.num_ativos_total)
            r4.metric("Rent. Ano", f"{cp.rent_ano_ponderada():+.2f}%")
        else:
            c1, c2, c3, c4, c5 = st.columns(5)
            c1.metric("Patrimonio Bruto", format_brl(cp.patrimonio_bruto_total))
            c2.metric("Patrimonio Liquido", format_brl(cp.patrimonio_liquido_total))
            c3.metric("Instituicoes", cp.num_instituicoes)
            c4.metric("Ativos", cp.num_ativos_total)
            c5.metric("Rent. Ano", f"{cp.rent_ano_ponderada():+.2f}%")

        st.divider()

        # Tabs de visualizacao
        tabs = st.tabs([
            "Por Instituicao",
            "Por Tipo",
            "Ranking Risco",
            "Top/Piores Rent.",
        ])

        with tabs[0]:
            _render_tab_instituicoes(cp, mobile)

        with tabs[1]:
            _render_tab_tipos(cp, mobile)

        with tabs[2]:
            _render_tab_risco(cp, mobile)

        with tabs[3]:
            _render_tab_rentabilidade(cp, mobile)

        # Botao download PDF
        if pdf_path and Path(pdf_path).exists():
            st.divider()
            with open(pdf_path, "rb") as f:
                st.download_button(
                    label="Baixar Relatorio PDF Consolidado",
                    data=f,
                    file_name="Relatorio_Consolidado.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                    type="primary",
                )

    render_footer()


def _render_tab_instituicoes(cp: ConsolidatedPortfolio, mobile: bool):
    """Tab de comparativo por instituicao."""
    dist = cp.distribuicao_por_instituicao()

    for inst_nome, d in dist.items():
        with st.expander(
            f"{inst_nome} - {format_brl(d['patrimonio_bruto'])} ({d['alocacao']:.1f}%)",
            expanded=not mobile,
        ):
            if mobile:
                m1, m2 = st.columns(2)
                m1.metric("Patrimonio", format_brl(d["patrimonio_bruto"]))
                m2.metric("Ativos", d["num_ativos"])
                m3, m4 = st.columns(2)
                m3.metric("Rent. Mes", f"{d['rent_mes']:+.2f}%")
                m4.metric("Rent. Ano", f"{d['rent_ano']:+.2f}%")
            else:
                mc1, mc2, mc3, mc4, mc5 = st.columns(5)
                mc1.metric("Patrimonio", format_brl(d["patrimonio_bruto"]))
                mc2.metric("Ativos", d["num_ativos"])
                mc3.metric("Rent. Mes", f"{d['rent_mes']:+.2f}%")
                mc4.metric("Rent. Ano", f"{d['rent_ano']:+.2f}%")
                mc5.metric("Rent. 12m", f"{d.get('rent_12m', 0):+.2f}%")

            if d.get("perfil"):
                st.caption(f"Perfil: {d['perfil']}")

            # Lista ativos da instituicao
            inst_ativos = [a for a in cp.todos_ativos if a.instituicao == inst_nome]
            if inst_ativos:
                rows = []
                for a in sorted(inst_ativos, key=lambda x: x.saldo_bruto, reverse=True):
                    rows.append({
                        "Ativo": a.ticker or a.nome[:30],
                        "Tipo": a.tipo,
                        "Saldo Bruto": f"R$ {a.saldo_bruto:,.2f}",
                        "% PL": f"{a.alocacao_pct:.1f}%",
                        "Rent. Mes": f"{a.rent_mes:+.2f}%" if a.rent_mes else "-",
                        "Rent. Ano": f"{a.rent_ano:+.2f}%" if a.rent_ano else "-",
                    })
                st.dataframe(rows, use_container_width=True, hide_index=True)


def _render_tab_tipos(cp: ConsolidatedPortfolio, mobile: bool):
    """Tab de distribuicao por tipo."""
    dist = cp.distribuicao_por_tipo()

    for tipo, d in dist.items():
        pct = d["alocacao"]
        st.markdown(f"**{tipo}** - {d['count']} ativos - {format_brl(d['saldo_bruto'])} ({pct:.1f}%)")
        st.progress(min(pct / 100, 1.0))


def _render_tab_risco(cp: ConsolidatedPortfolio, mobile: bool):
    """Tab de ranking de risco."""
    ranking = cp.ranking_risco_por_instituicao()

    for r in ranking:
        emoji = "🔴" if r["pct_risco"] > 30 else "🟡" if r["pct_risco"] > 10 else "🟢"
        st.markdown(
            f"{emoji} **{r['instituicao']}**: {r['ativos_risco']}/{r['ativos_total']} ativos de risco "
            f"({r['pct_risco']:.1f}% do patrimonio = {format_brl(r['saldo_risco'])})"
        )

    # Resumo geral
    total_risco = sum(r["saldo_risco"] for r in ranking)
    total = cp.patrimonio_bruto_total
    pct = (total_risco / total * 100) if total else 0
    st.divider()
    st.metric("Exposicao Total a Risco", f"{pct:.1f}%", delta=format_brl(total_risco))


def _render_tab_rentabilidade(cp: ConsolidatedPortfolio, mobile: bool):
    """Tab de melhores/piores rentabilidades."""
    col1, col2 = st.columns(2) if not mobile else (st.container(), st.container())

    with col1:
        st.markdown("**Top Melhores (Ano)**")
        for a in cp.melhores_rentabilidades()[:7]:
            nome = a["ticker"] or a["nome"][:20]
            st.markdown(f"📈 **{nome}** ({a['instituicao']}): {a['rent_ano']:+.2f}%")

    with col2:
        st.markdown("**Top Piores (Ano)**")
        for a in cp.piores_rentabilidades()[:7]:
            nome = a["ticker"] or a["nome"][:20]
            st.markdown(f"📉 **{nome}** ({a['instituicao']}): {a['rent_ano']:+.2f}%")
