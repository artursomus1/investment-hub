"""Página Portal de Notícias do HUB."""

import re
from datetime import datetime, timedelta

import streamlit as st

from agente_investimentos.ai_engine.gemini_client import analyze_period_summary_ai
from agente_investimentos.dashboard.session_persistence import (
    ensure_session_state,
    save_daily_summary_text, load_daily_summary_text,
    save_weekly_summary_text, load_weekly_summary_text,
    save_monthly_summary_text, load_monthly_summary_text,
)
from agente_investimentos.data_sources.market_news_scraper import (
    fetch_broad_news,
    get_all_news_flat,
    CATEGORIAS,
)
from agente_investimentos.hub.components import (
    render_news_card,
    render_hero_header,
    render_empty_state,
    render_footer,
)
from agente_investimentos.utils.formatters import parse_news_date

# Palavras-chave para scoring de relevancia financeira
_RELEVANCE_KEYWORDS = [
    "selic", "ipca", "inflacao", "juros", "pib", "dolar", "cambio",
    "ibovespa", "b3", "bolsa", "ações", "fii", "dividendo",
    "cdi", "renda fixa", "tesouro", "copom", "banco central",
    "investimento", "mercado", "fiscal", "deficit", "superavit",
    "lucro", "prejuizo", "receita", "balanco", "resultado",
]


def _relevance_score(article: dict) -> int:
    """Calcula score de relevancia financeira baseado no título."""
    título = article.get("título", "").lower()
    return sum(1 for kw in _RELEVANCE_KEYWORDS if kw in título)


def _filter_articles(articles: list, search: str, period: str, sort_by: str, fonte: str) -> list:
    """Aplica filtros na lista de artigos."""
    filtered = list(articles)

    # Filtro por texto
    if search:
        search_lower = search.lower()
        filtered = [
            a for a in filtered
            if search_lower in a.get("título", "").lower()
            or search_lower in a.get("fonte", "").lower()
        ]

    # Filtro por fonte
    if fonte and fonte != "Todas":
        filtered = [a for a in filtered if a.get("fonte", "") == fonte]

    # Filtro por período
    if period != "Todas":
        now = datetime.now()
        cutoff_map = {
            "Hoje": timedelta(days=1),
            "Ultimas 24h": timedelta(hours=24),
            "Últimos 3 dias": timedelta(days=3),
            "Ultima semana": timedelta(weeks=1),
        }
        cutoff_delta = cutoff_map.get(period)
        if cutoff_delta:
            cutoff = now - cutoff_delta
            result = []
            for a in filtered:
                dt = parse_news_date(a.get("data", ""))
                if dt is None:
                    result.append(a)  # mantém se não conseguiu parsear
                elif dt.replace(tzinfo=None) >= cutoff:
                    result.append(a)
            filtered = result

    # Ordenacao
    if sort_by == "Mais Recentes":
        filtered.sort(key=lambda a: a.get("data", ""), reverse=True)
    elif sort_by == "Mais Antigas":
        filtered.sort(key=lambda a: a.get("data", ""))
    elif sort_by == "Relevancia":
        filtered.sort(key=lambda a: _relevance_score(a), reverse=True)

    return filtered


def _get_all_sources(news_data: dict) -> list:
    """Extrai todas as fontes unicas das notícias."""
    sources = set()
    for articles in news_data.values():
        for a in articles:
            fonte = a.get("fonte", "").strip()
            if fonte:
                sources.add(fonte)
    return sorted(sources)


def _render_filter_bar(news_data: dict):
    """Renderiza barra de filtros e retorna os valores selecionados."""
    sources = _get_all_sources(news_data)

    col1, col2, col3, col4 = st.columns([3, 2, 2, 2])

    with col1:
        search = st.text_input(
            "Buscar",
            placeholder="Buscar por palavra-chave...",
            label_visibility="collapsed",
        )

    with col2:
        period = st.selectbox(
            "Periodo",
            options=["Todas", "Hoje", "Ultimas 24h", "Últimos 3 dias", "Ultima semana"],
            label_visibility="collapsed",
            help="Todas: sem filtro | Hoje: ultimas 24h | 3 dias: 72h | Semana: 7 dias",
        )

    with col3:
        sort_by = st.selectbox(
            "Ordenar por",
            options=["Mais Recentes", "Relevancia", "Mais Antigas"],
            label_visibility="collapsed",
        )

    with col4:
        fonte = st.selectbox(
            "Fonte",
            options=["Todas"] + sources,
            label_visibility="collapsed",
        )

    return search, period, sort_by, fonte


def render():
    """Renderiza a página de notícias."""
    ensure_session_state()
    render_hero_header("Portal de Notícias", "Notícias do mercado em tempo real via Google News")

    # Busca notícias (usa cache se disponível)
    force = st.session_state.get("force_refresh_news", False)
    if force:
        st.session_state["force_refresh_news"] = False

    with st.spinner("Carregando notícias..."):
        news_data = fetch_broad_news(force_refresh=force)
        st.session_state["news_data"] = news_data
        st.session_state["news_loaded_at"] = datetime.now().strftime("%H:%M")

    if not news_data:
        render_empty_state("Nenhuma noticia encontrada. Tente atualizar.")
        render_footer()
        return

    # Resumo Diario do Dia
    _render_daily_summary_section(news_data)

    st.divider()

    # Barra de filtros
    search, period, sort_by, fonte = _render_filter_bar(news_data)

    # Tabs por categoria
    tab_names = ["Todas"] + list(CATEGORIAS.keys())
    tabs = st.tabs(tab_names)

    # Tab "Todas"
    with tabs[0]:
        all_news = get_all_news_flat(news_data)
        filtered = _filter_articles(all_news, search, period, sort_by, fonte)
        if not filtered:
            render_empty_state("Nenhuma noticia encontrada com esses filtros.")
        else:
            st.markdown(
                f'<span class="news-stats">{len(filtered)} de {len(all_news)} notícias</span>',
                unsafe_allow_html=True,
            )
            for article in filtered:
                render_news_card(article)

    # Tabs por categoria
    for i, cat in enumerate(CATEGORIAS.keys()):
        with tabs[i + 1]:
            articles = news_data.get(cat, [])
            for a in articles:
                a["categoria"] = cat
            filtered = _filter_articles(articles, search, period, sort_by, fonte)
            if not filtered:
                render_empty_state(f"Nenhuma noticia de {cat} com esses filtros.")
            else:
                st.markdown(
                    f'<span class="news-stats">{len(filtered)} de {len(articles)} notícias de {cat}</span>',
                    unsafe_allow_html=True,
                )
                for article in filtered:
                    render_news_card(article)

    loaded_at = st.session_state.get("news_loaded_at", "")
    if loaded_at:
        st.caption(f"Ultima atualizacao: {loaded_at}")

    st.caption("Acesse **Impacto** para ver como as noticias afetam sua carteira")

    render_footer()


# ============================================================
# Resumo Diario
# ============================================================

_SUMMARY_SECTIONS_CONFIG = {
    "geopolítica": {
        "icon": "&#127758;",  # globe
        "css_class": "geopolítica",
        "title": "Geopolítica",
    },
    "ai": {
        "icon": "&#129302;",  # robot
        "css_class": "ai",
        "title": "Inteligencia Artificial",
    },
    "economia": {
        "icon": "&#128200;",  # chart
        "css_class": "economia",
        "title": "Economia",
    },
}


def _filter_news_by_period(articles: list, period: str) -> list:
    """Filtra noticias por periodo usando parse_news_date().

    Args:
        articles: Lista de noticias
        period: "diario" | "semanal" | "mensal"

    Returns:
        Lista filtrada de noticias dentro do periodo
    """
    delta_map = {
        "diario": timedelta(days=1),
        "semanal": timedelta(days=7),
        "mensal": timedelta(days=30),
    }
    delta = delta_map.get(period, timedelta(days=1))
    cutoff = datetime.now() - delta

    filtered = []
    for a in articles:
        dt = parse_news_date(a.get("data", ""))
        if dt is None:
            filtered.append(a)  # mantém se não conseguiu parsear
        elif dt.replace(tzinfo=None) >= cutoff:
            filtered.append(a)
    return filtered


# Mapeamento de periodo -> chave de session_state e funcoes de persistencia
_PERIOD_CONFIG = {
    "diario": {
        "session_key": "daily_summary_text",
        "save_fn": save_daily_summary_text,
        "load_fn": load_daily_summary_text,
        "label": "Resumo Diario",
        "btn_label": "Diario",
    },
    "semanal": {
        "session_key": "weekly_summary_text",
        "save_fn": save_weekly_summary_text,
        "load_fn": load_weekly_summary_text,
        "label": "Resumo Semanal",
        "btn_label": "Semanal",
    },
    "mensal": {
        "session_key": "monthly_summary_text",
        "save_fn": save_monthly_summary_text,
        "load_fn": load_monthly_summary_text,
        "label": "Resumo Mensal",
        "btn_label": "Mensal",
    },
}


def _render_daily_summary_section(news_data: dict):
    """Renderiza a secao de resumo com seletor de periodo e botao gerar."""
    st.subheader("Resumos por Periodo")

    # Carrega resumos salvos se não estiverem no session_state
    for period, cfg in _PERIOD_CONFIG.items():
        if cfg["session_key"] not in st.session_state:
            saved = cfg["load_fn"]()
            if saved:
                st.session_state[cfg["session_key"]] = saved

    # Seletor de periodo + botao gerar
    col_sel, col_btn = st.columns([1, 1])
    with col_sel:
        selected = st.selectbox(
            "Periodo",
            options=list(_PERIOD_CONFIG.keys()),
            format_func=lambda p: _PERIOD_CONFIG[p]["btn_label"],
            index=list(_PERIOD_CONFIG.keys()).index(
                st.session_state.get("active_summary_period", "diario")
            ),
            label_visibility="collapsed",
        )
    with col_btn:
        generate = st.button(
            f"Gerar {_PERIOD_CONFIG[selected]['label']}",
            type="primary",
            use_container_width=True,
        )

    # Atualiza periodo ativo ao trocar seletor
    st.session_state["active_summary_period"] = selected
    cfg = _PERIOD_CONFIG[selected]

    # Gerar resumo ao clicar
    if generate:
        all_news = get_all_news_flat(news_data)
        filtered = _filter_news_by_period(all_news, selected)

        if len(filtered) < 3:
            st.warning(
                f"Apenas {len(filtered)} noticia(s) no periodo ({cfg['btn_label']}). "
                "O RSS pode nao ter historico suficiente."
            )
            if not filtered:
                return

        with st.spinner(f"Gerando {cfg['label'].lower()} via Gemini ({len(filtered)} noticias)..."):
            summary_text = analyze_period_summary_ai(filtered, selected)
            if summary_text.startswith("[ERRO]"):
                st.error(summary_text.replace("[ERRO] ", ""))
                st.info("Dica: verifique sua chave Gemini, conexao de internet, ou tente novamente em alguns segundos (rate limit).")
            else:
                st.session_state[cfg["session_key"]] = summary_text
                cfg["save_fn"](summary_text)

    # Exibir resumo do periodo selecionado
    summary_text = st.session_state.get(cfg["session_key"])
    if summary_text and not summary_text.startswith("[ERRO]"):
        st.markdown(f"#### {cfg['label']}")
        _render_summary_cards(summary_text)
    else:
        st.caption("Resumo via IA focado em Geopolitica, Inteligencia Artificial e Economia")


def _parse_summary_sections(text: str) -> dict:
    """Separa o texto do resumo nas 3 seções esperadas."""
    header_patterns = [
        re.compile(r'^\s*\*\*\s*(GEOPOLITICA|INTELIGENCIA ARTIFICIAL|ECONOMIA)\s*\*\*\s*$', re.IGNORECASE),
        re.compile(r'^\s*#{2,3}\s*(GEOPOLITICA|INTELIGENCIA ARTIFICIAL|ECONOMIA)\s*$', re.IGNORECASE),
    ]

    sections = {}
    current_key = None
    current_lines = []

    for line in text.split('\n'):
        matched_key = None
        for pat in header_patterns:
            m = pat.match(line)
            if m:
                title = m.group(1).strip().upper()
                if "GEOPOLITICA" in title or "GEOPOL" in title:
                    matched_key = "geopolítica"
                elif "INTELIGENCIA" in title or "ARTIFICIAL" in title or "IA" == title:
                    matched_key = "ai"
                elif "ECONOMIA" in title or "ECONO" in title:
                    matched_key = "economia"
                break

        if matched_key:
            if current_key and current_lines:
                sections[current_key] = '\n'.join(current_lines).strip()
            current_key = matched_key
            current_lines = []
        else:
            if current_key is not None:
                current_lines.append(line)

    if current_key and current_lines:
        sections[current_key] = '\n'.join(current_lines).strip()

    return sections


def _render_summary_cards(text: str):
    """Renderiza os 3 cards do resumo diario."""
    sections = _parse_summary_sections(text)

    if not sections:
        # Fallback: mostra texto puro
        st.markdown(text)
        return

    cols = st.columns(3)
    for i, (key, config) in enumerate(_SUMMARY_SECTIONS_CONFIG.items()):
        content = sections.get(key, "Sem informações disponíveis.")
        # Converte bold markdown para HTML
        content_html = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', content)
        # Converte quebras de linha em paragrafos
        paragraphs = [p.strip() for p in content_html.split('\n') if p.strip()]
        body_html = ''.join(f'<p>{p}</p>' for p in paragraphs)

        with cols[i]:
            st.markdown(f"""
            <div class="daily-summary-card {config['css_class']}">
                <div class="daily-summary-card-header">
                    <div class="daily-summary-card-icon">{config['icon']}</div>
                    <h4>{config['title']}</h4>
                </div>
                <div class="daily-summary-card-body">
                    {body_html}
                </div>
            </div>
            """, unsafe_allow_html=True)
