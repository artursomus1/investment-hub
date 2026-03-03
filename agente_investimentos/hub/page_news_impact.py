"""Página de Impacto das Notícias na Carteira."""

import re
from collections import defaultdict

import streamlit as st

from agente_investimentos.ai_engine.gemini_client import analyze_news_impact_ai
from agente_investimentos.data_sources.market_news_scraper import fetch_broad_news, get_all_news_flat
from agente_investimentos.dashboard.session_persistence import ensure_session_state, save_impact_text
from agente_investimentos.hub.components import render_hero_header, render_footer, format_brl, is_mobile
from agente_investimentos.utils.formatters import parse_news_date


# Configuração visual de cada secao de impacto
_SECTION_CONFIG = {
    "contexto": {
        "icon": "&#127758;",   # globe
        "css_class": "panorama",
        "title_prefix": "Contexto Macro e Politico",
        "emoji": "🌍",
    },
    "setorial": {
        "icon": "&#127981;",   # factory
        "css_class": "setorial",
        "title_prefix": "Mapa de Impacto Setorial",
        "emoji": "🏭",
    },
    "risco": {
        "icon": "&#9888;",     # warning
        "css_class": "risco",
        "title_prefix": "Ativos em Risco",
        "emoji": "⚠️",
    },
    "favorecido": {
        "icon": "&#9650;",     # triangle up
        "css_class": "favorecido",
        "title_prefix": "Ativos Favorecidos",
        "emoji": "📈",
    },
    "cenarios": {
        "icon": "&#128302;",   # crystal ball
        "css_class": "cenarios",
        "title_prefix": "Cenarios Prospectivos",
        "emoji": "🔮",
    },
    "termometro": {
        "icon": "&#127777;",   # thermometer
        "css_class": "termometro",
        "title_prefix": "Termometro de Risco",
        "emoji": "🌡️",
    },
    "ações": {
        "icon": "&#9889;",     # lightning
        "css_class": "ações",
        "title_prefix": "Acoes Recomendadas",
        "emoji": "⚡",
    },
    "resumo": {
        "icon": "&#9733;",     # star
        "css_class": "resumo",
        "title_prefix": "Resumo Executivo",
        "emoji": "⭐",
    },
}


def _classify_section(title: str) -> str:
    """Identifica o tipo da secao pelo título."""
    t = title.lower()
    # Contexto macro (antiga "panorama")
    if "contexto" in t or "macroeconomic" in t or ("cenario" in t and ("macro" in t or "politic" in t or "fiscal" in t)):
        return "contexto"
    # Mapa setorial
    if "setorial" in t or "setor" in t and "mapa" in t:
        return "setorial"
    # Cenarios prospectivos (E se...)
    if ("cenario" in t and ("prospectiv" in t or "bull" in t or "bear" in t or "otimist" in t or "pessimist" in t)) or "prospectiv" in t:
        return "cenarios"
    # Termometro de risco
    if "termometro" in t or ("nivel" in t and "risco" in t and "carteira" in t) or "vulnerabil" in t:
        return "termometro"
    # Ativos em risco
    if "risco" in t or "negativ" in t or "ameac" in t:
        return "risco"
    # Ativos favorecidos
    if "favorec" in t or "positiv" in t or "oportunid" in t:
        return "favorecido"
    # Acoes recomendadas
    if "aco" in t and ("recomend" in t or "suger" in t) or "recomenda" in t:
        return "ações"
    # Resumo executivo
    if "resumo" in t or "executivo" in t or "conclus" in t:
        return "resumo"
    return "contexto"


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
    """Renderiza um card de impacto estilizado (desktop)."""
    config = _SECTION_CONFIG.get(section_type, _SECTION_CONFIG["contexto"])
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


def _render_impact_card_mobile(title: str, content: str, section_type: str):
    """Renderiza um card de impacto como expander colapsavel (mobile)."""
    config = _SECTION_CONFIG.get(section_type, _SECTION_CONFIG["contexto"])
    emoji = config.get("emoji", "")

    # Resumo executivo sempre aberto no mobile
    expanded = section_type == "resumo"

    with st.expander(f"{emoji} {title}", expanded=expanded):
        st.markdown(content)


def render():
    """Renderiza a página de impacto das notícias."""
    ensure_session_state()
    mobile = is_mobile()

    render_hero_header(
        "Impacto das Noticias" if mobile else "Impacto das Notícias na Carteira",
        "" if mobile else "Análise via IA de como as notícias recentes afetam seus investimentos",
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

    # Info da carteira em KPIs — 2 colunas no mobile, 4 no desktop
    if mobile:
        r1c1, r1c2 = st.columns(2)
        r1c1.metric("Cliente", portfolio.client_code)
        r1c2.metric("Ativos", portfolio.num_assets)
        r2c1, r2c2 = st.columns(2)
        r2c1.metric("Patrimonio", format_brl(portfolio.total_bruto))
        r2c2.metric("Rent. Mes", f"{portfolio_analysis.get('rent_mes_ponderada', 0):+.2f}%")
    else:
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

        max_per_cat = 5 if mobile else 8
        for cat, articles in sorted(by_cat.items()):
            st.markdown(f"**{cat}** ({len(articles)} noticias)")
            for a in articles[:max_per_cat]:
                fonte = a.get("fonte", "")
                data_str = a.get("data", "")
                dt = parse_news_date(data_str)
                data_fmt = dt.strftime("%d/%m %H:%M") if dt else ""
                if mobile:
                    # Mobile: so titulo e fonte, sem data longa
                    meta = f" *({fonte})*" if fonte else ""
                    st.markdown(f"- {a.get('título', '')}{meta}")
                else:
                    meta = f" - {fonte}" if fonte else ""
                    if data_fmt:
                        meta += f" ({data_fmt})"
                    st.markdown(f"- {a.get('título', '')}{meta}")
            remaining = len(articles) - max_per_cat
            if remaining > 0:
                st.caption(f"... e mais {remaining} noticias de {cat}")
            st.markdown("---")

    # Botao para gerar análise — full width no mobile
    if mobile:
        run_analysis = st.button(
            "Gerar Analise de Impacto",
            type="primary",
            use_container_width=True,
        )
        st.caption(f"{len(all_news)} noticias analisadas")
    else:
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
        with st.spinner("Gerando analise profunda de impacto (8 secoes) via Gemini — pode levar ate 30s..."):
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

        # Mini-resumo com contagem de ativos e nivel de risco
        sections = _split_sections(impact_text)
        risco_count = 0
        favorecido_count = 0
        nivel_risco = ""
        urgencia = ""
        for title, content in sections:
            stype = _classify_section(title)
            if stype == "risco":
                risco_count = len(re.findall(r'(?:^|\n)\s*[-*]\s', content))
            elif stype == "favorecido":
                favorecido_count = len(re.findall(r'(?:^|\n)\s*[-*]\s', content))
            elif stype == "termometro":
                # Extrai nivel geral de risco
                for nivel in ["CRITICO", "ELEVADO", "MODERADO", "BAIXO"]:
                    if nivel in content.upper():
                        nivel_risco = nivel.capitalize()
                        break
                # Extrai indice de urgencia
                urgencia_match = re.search(r'(?:urgencia|indice)[^\d]*(\d+)\s*/?\s*10', content, re.IGNORECASE)
                if urgencia_match:
                    urgencia = f"{urgencia_match.group(1)}/10"

        # Metricas — 2x2 no mobile, 1x4 no desktop
        if mobile:
            m1, m2 = st.columns(2)
            m1.metric("Em Risco", risco_count, delta="atencao", delta_color="inverse")
            m2.metric("Favorecidos", favorecido_count, delta="oportunidade", delta_color="normal")
            m3, m4 = st.columns(2)
            if nivel_risco:
                delta_color = "inverse" if nivel_risco in ("Critico", "Elevado") else "normal"
                m3.metric("Risco", nivel_risco, delta="carteira", delta_color=delta_color)
            else:
                m3.metric("Secoes", len(sections))
            if urgencia:
                m4.metric("Urgencia", urgencia)
            else:
                m4.metric("Noticias", len(all_news))
        else:
            cols = st.columns(4)
            cols[0].metric("Ativos em Risco", risco_count, delta="atencao", delta_color="inverse")
            cols[1].metric("Ativos Favorecidos", favorecido_count, delta="oportunidade", delta_color="normal")
            if nivel_risco:
                delta_color = "inverse" if nivel_risco in ("Critico", "Elevado") else "normal"
                cols[2].metric("Nivel de Risco", nivel_risco, delta="carteira", delta_color=delta_color)
            else:
                cols[2].metric("Secoes", len(sections))
            if urgencia:
                cols[3].metric("Urgencia de Acao", urgencia)
            else:
                cols[3].metric("Noticias Analisadas", len(all_news))

        _render_impact_analysis(impact_text, mobile=mobile)

        if mobile:
            st.success("Acesse **Migracao** para estrategias de mitigacao.")
        else:
            st.success(
                "Proximo passo: acesse **Migracao** no menu lateral para gerar estrategias "
                "de mitigacao e rebalanceamento baseadas nesta analise."
            )

    render_footer()


def _render_impact_analysis(text: str, mobile: bool = False):
    """Renderiza a análise de impacto com cards visuais."""
    sections = _split_sections(text)

    if sections:
        for title, content in sections:
            section_type = _classify_section(title)
            if mobile:
                _render_impact_card_mobile(title, content, section_type)
            else:
                _render_impact_card(title, content, section_type)
    else:
        # Fallback: renderiza como markdown dentro de um card generico
        if mobile:
            _render_impact_card_mobile("Análise de Impacto", text, "contexto")
        else:
            _render_impact_card("Análise de Impacto", text, "contexto")


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
