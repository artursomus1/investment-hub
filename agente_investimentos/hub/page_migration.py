"""Página de Recomendações de Migração/Rebalanceamento."""

import streamlit as st

from agente_investimentos.ai_engine.gemini_client import analyze_migration_ai
from agente_investimentos.dashboard.session_persistence import ensure_session_state, save_migration_text
from agente_investimentos.hub.components import format_brl, render_hero_header, render_footer


def render():
    """Renderiza a página de recomendações de migração."""
    ensure_session_state()
    render_hero_header("Recomendações de Migração", "Sugestoes de rebalanceamento e migração de ativos via IA")

    # Verifica se tem carteira carregada
    result = st.session_state.get("last_result")
    if not result:
        st.warning("Nenhuma carteira carregada. Execute uma análise em **Análise de Carteira** primeiro.")
        st.stop()

    portfolio_analysis = result["portfolio_analysis"]
    asset_analyses = result["asset_analyses"]
    macro = result.get("macro", {}) or {}
    portfolio = result["portfolio"]

    st.info(f"Carteira carregada: **{portfolio.client_code}** | {portfolio.num_assets} ativos | "
            f"R$ {portfolio.total_bruto:,.2f}")

    # Mostra alocacao atual resumida
    st.divider()
    _render_current_allocation(portfolio_analysis)

    st.divider()

    # Opcao de usar contexto de impacto de notícias
    news_impact_text = st.session_state.get("news_impact_text", "")
    use_impact = False
    if news_impact_text:
        use_impact = st.checkbox(
            "Usar análise de impacto das notícias como contexto adicional",
            value=True,
            help="Inclui o resultado da análise de impacto para recomendações mais contextualizadas",
        )

    # Botao para gerar
    if st.button("Gerar Recomendações de Migração", type="primary", use_container_width=False):
        impact_ctx = news_impact_text if use_impact else ""
        with st.spinner("Gerando recomendações de migração via Gemini..."):
            migration_text = analyze_migration_ai(
                portfolio_analysis=portfolio_analysis,
                asset_analyses=asset_analyses,
                macro=macro,
                news_impact_text=impact_ctx,
            )
            if migration_text.startswith("[ERRO]"):
                st.error(migration_text.replace("[ERRO] ", ""))
                st.info("Dica: verifique sua chave Gemini, conexao de internet, ou tente novamente em alguns segundos (rate limit).")
            else:
                st.session_state["migration_text"] = migration_text
                save_migration_text(migration_text)

    # Renderiza resultado
    migration_text = st.session_state.get("migration_text")
    if migration_text and not migration_text.startswith("[ERRO]"):
        st.divider()
        _render_migration_analysis(migration_text)

    render_footer()


def _render_current_allocation(pa: dict):
    """Mostra a alocacao atual da carteira."""
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Alocacao por Tipo")
        dist_tipo = pa.get("distribuição_tipo", {})
        if dist_tipo:
            for tipo, dados in dist_tipo.items():
                pct = dados["alocacao"]
                st.markdown(
                    f"**{tipo}**: {pct:.1f}% (R$ {dados['saldo']:,.2f}) - {dados['count']} ativo(s)"
                )
        else:
            st.info("Dados de alocacao não disponíveis.")

    with col2:
        st.subheader("Alocacao por Setor")
        dist_setor = pa.get("distribuição_setor", {})
        if dist_setor:
            # Mostra top 8 setores
            sorted_setores = sorted(dist_setor.items(), key=lambda x: x[1]["alocacao"], reverse=True)
            for setor, dados in sorted_setores[:8]:
                pct = dados["alocacao"]
                st.markdown(f"**{setor}**: {pct:.1f}%")
            if len(sorted_setores) > 8:
                st.caption(f"... e mais {len(sorted_setores) - 8} setores")
        else:
            st.info("Dados setoriais não disponíveis.")


def _render_migration_analysis(text: str):
    """Renderiza as recomendações de migração formatadas."""
    import re

    sections = _split_migration_sections(text)

    if len(sections) >= 2:
        for title, content in sections:
            with st.expander(title, expanded=True):
                st.markdown(content)
    else:
        st.markdown(text)


def _split_migration_sections(text: str):
    """Separa texto de migração em seções (parser robusto)."""
    import re

    header_patterns = [
        re.compile(r'^\s*#{2,3}\s*\d*\.?\s*(.+?)\s*$'),
        re.compile(r'^\s*\*\*\d+[\.\)]\s*(.+?)\*\*\s*$'),
        re.compile(r'^\s*\d+[\.\)]\s*\*\*(.+?)\*\*\s*$'),
        re.compile(r'^\s*\*\*([A-Z\u00C0-\u00FF][^*]{2,})\*\*\s*$'),
    ]

    lines = text.split('\n')
    sections = []
    current_title = None
    current_lines = []

    for line in lines:
        matched_title = None
        for pat in header_patterns:
            m = pat.match(line)
            if m:
                matched_title = m.group(1).strip().rstrip(':')
                break

        if matched_title:
            if current_title and current_lines:
                content = '\n'.join(current_lines).strip()
                if content:
                    sections.append((current_title, content))
            current_title = matched_title
            current_lines = []
        else:
            if current_title is not None:
                current_lines.append(line)

    if current_title and current_lines:
        content = '\n'.join(current_lines).strip()
        if content:
            sections.append((current_title, content))

    return sections
