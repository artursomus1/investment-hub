"""Página de Impacto das Notícias na Carteira."""

import re
from collections import defaultdict

import streamlit as st

from agente_investimentos.ai_engine.gemini_client import analyze_news_impact_ai
from agente_investimentos.data_sources.market_news_scraper import fetch_broad_news, get_all_news_flat
from agente_investimentos.dashboard.session_persistence import ensure_session_state, save_impact_text
from agente_investimentos.hub.components import render_hero_header, render_footer, format_brl
from agente_investimentos.utils.formatters import parse_news_date


# Configuração visual de cada secao de impacto
_SECTION_CONFIG = {
    "panorama": {
        "icon": "&#127758;",   # globe
        "css_class": "panorama",
        "title_prefix": "Panorama Geral",
    },
    "risco": {
        "icon": "&#9888;",     # warning
        "css_class": "risco",
        "title_prefix": "Ativos em Risco",
    },
    "favorecido": {
        "icon": "&#9650;",     # triangle up
        "css_class": "favorecido",
        "title_prefix": "Ativos Favorecidos",
    },
    "ações": {
        "icon": "&#9889;",     # lightning
        "css_class": "ações",
        "title_prefix": "Ações Recomendadas",
    },
    "resumo": {
        "icon": "&#9733;",     # star
        "css_class": "resumo",
        "title_prefix": "Resumo Executivo",
    },
}


def _classify_section(title: str) -> str:
    """Identifica o tipo da secao pelo título."""
    t = title.lower()
    if "panorama" in t or "cenario" in t or "geral" in t:
        return "panorama"
    if "risco" in t or "negativ" in t or "ameac" in t:
        return "risco"
    if "favorec" in t or "positiv" in t or "oportunid" in t:
        return "favorecido"
    if "aco" in t and ("recomend" in t or "suger" in t) or "recomenda" in t:
        return "ações"
    if "resumo" in t or "executivo" in t or "conclus" in t:
        return "resumo"
    return "panorama"


def _md_to_html(text: str) -> str:
    """Converte markdown para HTML seguro."""
    # Converte bold
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    # Converte italic
    text = re.sub(r'(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)', r'<em>\1</em>', text)
    # Converte listas
    lines = text.split('\n')
    result = []
    in_list = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith('- ') or stripped.startswith('* '):
            if not in_list:
                result.append('<ul>')
                in_list = True
            item = stripped[2:]
            result.append(f'<li>{item}</li>')
        else:
            if in_list:
                result.append('</ul>')
                in_list = False
            if stripped:
                result.append(f'<p>{stripped}</p>')
    if in_list:
        result.append('</ul>')
    return '\n'.join(result)


def _render_impact_card(title: str, content: str, section_type: str):
    """Renderiza um card de impacto estilizado."""
    config = _SECTION_CONFIG.get(section_type, _SECTION_CONFIG["panorama"])
    icon = config["icon"]
    css_class = config["css_class"]

    content_html = _md_to_html(content)

    st.markdown(f"""
    <div class="impact-card {css_class}">
        <div class="impact-card-header">
            <div class="impact-card-icon">{icon}</div>
            <h3>{title}</h3>
        </div>
        <div class="impact-card-body">
            {content_html}
        </div>
    </div>
    """, unsafe_allow_html=True)


def render():
    """Renderiza a página de impacto das notícias."""
    ensure_session_state()
    render_hero_header(
        "Impacto das Notícias na Carteira",
        "Análise via IA de como as notícias recentes afetam seus investimentos",
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

    # Info da carteira em KPIs
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Cliente", portfolio.client_code)
    c2.metric("Ativos", portfolio.num_assets)
    c3.metric("Patrimônio", format_brl(portfolio.total_bruto))
    c4.metric("Rent. Mês", f"{portfolio_analysis.get('rent_mes_ponderada', 0):+.2f}%")

    # Busca notícias
    news_data = st.session_state.get("news_data")
    if not news_data:
        with st.spinner("Carregando notícias..."):
            news_data = fetch_broad_news()
            st.session_state["news_data"] = news_data

    if not news_data:
        st.warning("Nenhuma noticia disponível. Va em **Notícias** para carregar.")
        st.stop()

    all_news = get_all_news_flat(news_data)

    st.divider()

    # Expander com manchetes recentes por categoria
    with st.expander(f"Manchetes Recentes ({len(all_news)} noticias)", expanded=False):
        # Agrupar por categoria
        by_cat = defaultdict(list)
        for n in all_news:
            cat = n.get("categoria", "Geral")
            by_cat[cat].append(n)

        for cat, articles in sorted(by_cat.items()):
            st.markdown(f"**{cat}** ({len(articles)} noticias)")
            for a in articles[:8]:
                fonte = a.get("fonte", "")
                data_str = a.get("data", "")
                dt = parse_news_date(data_str)
                data_fmt = dt.strftime("%d/%m %H:%M") if dt else ""
                meta = f" - {fonte}" if fonte else ""
                if data_fmt:
                    meta += f" ({data_fmt})"
                st.markdown(f"- {a.get('título', '')}{meta}")
            if len(articles) > 8:
                st.caption(f"... e mais {len(articles) - 8} noticias de {cat}")
            st.markdown("---")

    # Botao para gerar análise
    col_btn, col_info = st.columns([1, 3])
    with col_btn:
        run_analysis = st.button(
            "Gerar Análise de Impacto",
            type="primary",
            use_container_width=True,
        )
    with col_info:
        st.caption(f"{len(all_news)} notícias serão analisadas contra a carteira do cliente")

    if run_analysis:
        with st.spinner("Analisando impacto das notícias na carteira via Gemini..."):
            impact_text = analyze_news_impact_ai(
                news_articles=all_news,
                portfolio_analysis=portfolio_analysis,
                asset_analyses=asset_analyses,
                macro=macro,
            )
            if impact_text.startswith("[ERRO]"):
                st.error(impact_text.replace("[ERRO] ", ""))
                st.info("Dica: verifique sua chave Gemini, conexao de internet, ou tente novamente em alguns segundos (rate limit).")
            else:
                st.session_state["news_impact_text"] = impact_text
                save_impact_text(impact_text)

    # Renderiza resultado
    impact_text = st.session_state.get("news_impact_text")
    if impact_text and not impact_text.startswith("[ERRO]"):
        st.divider()
        _render_impact_analysis(impact_text)
        st.info(
            "Para ver estrategias de mitigacao e rebalanceamento baseadas nesta analise, "
            "acesse a pagina **Migracao** no menu lateral."
        )

    render_footer()


def _render_impact_analysis(text: str):
    """Renderiza a análise de impacto com cards visuais."""
    sections = _split_sections(text)

    if sections:
        for title, content in sections:
            section_type = _classify_section(title)
            _render_impact_card(title, content, section_type)
    else:
        # Fallback: renderiza como markdown dentro de um card generico
        _render_impact_card("Análise de Impacto", text, "panorama")


def _split_sections(text: str) -> list:
    """Separa o texto em seções baseado em headers markdown.

    Suporta multiplos formatos de header do Gemini:
    - **1. TITULO**
    - **TITULO**
    - ## TITULO
    - ### TITULO
    - 1. **TITULO**
    - **1) TITULO**
    """
    # Padroes de header (ordem de prioridade)
    header_patterns = [
        re.compile(r'^\s*#{2,3}\s*\d*\.?\s*(.+?)\s*$'),          # ## TITULO ou ### 1. TITULO
        re.compile(r'^\s*\*\*\d+[\.\)]\s*(.+?)\*\*\s*$'),        # **1. TITULO** ou **1) TITULO**
        re.compile(r'^\s*\d+[\.\)]\s*\*\*(.+?)\*\*\s*$'),        # 1. **TITULO** ou 1) **TITULO**
        re.compile(r'^\s*\*\*([A-Z\u00C0-\u00FF][^*]{2,})\*\*\s*$'),  # **TITULO EM MAIUSCULA**
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
            # Salva secao anterior se existir
            if current_title and current_lines:
                content = '\n'.join(current_lines).strip()
                if content:
                    sections.append((current_title, content))
            current_title = matched_title
            current_lines = []
        else:
            if current_title is not None:
                current_lines.append(line)

    # Salva última secao
    if current_title and current_lines:
        content = '\n'.join(current_lines).strip()
        if content:
            sections.append((current_title, content))

    if len(sections) < 2:
        return []

    return sections
