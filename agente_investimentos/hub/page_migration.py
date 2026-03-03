"""Página de Recomendações de Migração/Rebalanceamento."""

import re

import streamlit as st

from agente_investimentos.ai_engine.gemini_client import analyze_migration_ai
from agente_investimentos.dashboard.session_persistence import ensure_session_state, save_migration_text
from agente_investimentos.hub.components import format_brl, render_hero_header, render_footer


def render():
    """Renderiza a página de recomendações de migração."""
    ensure_session_state()
    render_hero_header(
        "Estrategias de Mitigacao e Migracao",
        "Mitigacao de riscos, rebalanceamento e migracao de ativos via IA",
    )

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

    # Banner de contexto de impacto — sem checkbox, usa automaticamente se disponível
    news_impact_text = st.session_state.get("news_impact_text", "")
    if news_impact_text:
        st.success(
            "Contexto de impacto das noticias **integrado** automaticamente. "
            "Os riscos identificados serao usados para gerar estrategias de mitigacao."
        )
    else:
        st.warning(
            "Nenhuma analise de impacto disponivel. Recomendamos executar a analise em "
            "**Impacto das Noticias** primeiro para resultados mais completos. "
            "Voce pode gerar mesmo assim — o foco sera em riscos estruturais da carteira."
        )

    # Botao para gerar
    if st.button("Gerar Estrategias de Mitigacao e Migracao", type="primary", use_container_width=False):
        with st.spinner("Gerando estrategias de mitigacao e migracao via Gemini..."):
            migration_text = analyze_migration_ai(
                portfolio_analysis=portfolio_analysis,
                asset_analyses=asset_analyses,
                macro=macro,
                news_impact_text=news_impact_text,
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


def _is_mitigation_section(title: str) -> bool:
    """Verifica se a secao e de mitigacao."""
    t = title.lower()
    return "mitigac" in t or "mitigaç" in t


def _render_migration_analysis(text: str):
    """Renderiza as recomendações de migração formatadas."""
    sections = _split_migration_sections(text)

    if len(sections) >= 2:
        for title, content in sections:
            if _is_mitigation_section(title):
                # Destaque visual para secao de mitigacao
                st.markdown(
                    f'<div style="border-left: 4px solid #e74c3c; padding: 0.5rem 1rem; '
                    f'background-color: rgba(231,76,60,0.05); border-radius: 4px; margin-bottom: 1rem;">'
                    f'<h4 style="color: #e74c3c; margin-top: 0;">&#9888; {title}</h4>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
                st.markdown(content)
                st.divider()
            else:
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
