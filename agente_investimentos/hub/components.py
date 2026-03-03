"""Componentes reutilizaveis do HUB."""

import streamlit as st
from datetime import datetime


# === Mobile Detection ===

def is_mobile() -> bool:
    """Detecta se o acesso e mobile baseado na largura da tela.

    Usa JavaScript para capturar a largura do viewport e grava no session_state.
    Na primeira carga retorna False (desktop) ate o JS rodar.
    """
    # Injeta JS que detecta largura e envia pro Streamlit via query param
    _inject_mobile_detector()
    return st.session_state.get("is_mobile", False)


def _inject_mobile_detector():
    """Injeta script JS que detecta viewport e atualiza session_state."""
    # Se ja detectou nesta sessao, nao re-injeta
    if "mobile_detected" in st.session_state:
        return

    # Usa st.query_params para receber a largura do JS
    params = st.query_params
    screen_w = params.get("_sw")
    if screen_w:
        try:
            width = int(screen_w)
            st.session_state["is_mobile"] = width < 768
            st.session_state["is_tablet"] = 768 <= width < 1024
            st.session_state["screen_width"] = width
            st.session_state["mobile_detected"] = True
            return
        except (ValueError, TypeError):
            pass

    # Injeta JS para capturar largura e recarregar com query param
    st.markdown("""
    <script>
    (function() {
        const url = new URL(window.location);
        const sw = window.innerWidth || document.documentElement.clientWidth;
        if (!url.searchParams.has('_sw')) {
            url.searchParams.set('_sw', sw.toString());
            window.location.replace(url.toString());
        }
    })();
    </script>
    """, unsafe_allow_html=True)


# === Category Badge ===

_BADGE_CLASSES = {
    "Economia": "badge-economia",
    "Politica": "badge-política",
    "Mercado Financeiro": "badge-mercado",
    "Esportes": "badge-esportes",
    "Todas": "badge-todas",
}


def category_badge(categoria: str) -> str:
    """Retorna HTML de badge colorido por categoria."""
    css_class = _BADGE_CLASSES.get(categoria, "badge-todas")
    return f'<span class="badge {css_class}">{categoria}</span>'


def impact_badge(tipo: str) -> str:
    """Retorna HTML de badge de impacto (positivo/negativo/neutro)."""
    tipo_lower = tipo.lower()
    if "positiv" in tipo_lower or "favorec" in tipo_lower:
        return '<span class="badge badge-positivo">Positivo</span>'
    elif "negativ" in tipo_lower or "risco" in tipo_lower:
        return '<span class="badge badge-negativo">Negativo</span>'
    return '<span class="badge badge-neutro">Neutro</span>'


# === News Card ===

def render_news_card(article: dict):
    """Renderiza um card de noticia."""
    título = article.get("título", "Sem título")
    link = article.get("link", "#")
    data = article.get("data", "")[:22]
    fonte = article.get("fonte", "")
    categoria = article.get("categoria", "")

    badge_html = category_badge(categoria) if categoria else ""
    fonte_html = f" | {fonte}" if fonte else ""

    st.markdown(f"""
    <div class="news-card">
        <div class="news-card-title">
            <a href="{link}" target="_blank" rel="noopener">{título}</a>
        </div>
        <div class="news-card-meta">
            {badge_html}{fonte_html} | {data}
        </div>
    </div>
    """, unsafe_allow_html=True)


# === KPI Row ===

def render_kpi_row(kpis: list):
    """Renderiza uma linha de KPIs.

    Args:
        kpis: Lista de tuples (label, value, delta=None, delta_color="normal")
    """
    cols = st.columns(len(kpis))
    for col, kpi in zip(cols, kpis):
        label = kpi[0]
        value = kpi[1]
        delta = kpi[2] if len(kpi) > 2 else None
        delta_color = kpi[3] if len(kpi) > 3 else "normal"
        if delta is not None:
            col.metric(label, value, delta=delta, delta_color=delta_color)
        else:
            col.metric(label, value)


# === Format BRL ===

def format_brl(value: float) -> str:
    """Formata valor em BRL."""
    if value >= 1_000_000:
        return f"R$ {value/1_000_000:,.2f}M"
    elif value >= 1_000:
        return f"R$ {value/1_000:,.1f}K"
    return f"R$ {value:,.2f}"


# === Impact Section ===

def render_impact_section(title: str, content: str):
    """Renderiza uma secao de impacto formatada."""
    st.markdown(f"""
    <div class="impact-section">
        <h4>{title}</h4>
        <div>{content}</div>
    </div>
    """, unsafe_allow_html=True)


# === Hero Header ===

def render_hero_header(title: str, subtitle: str = "", badge: str = ""):
    """Renderiza hero header com gradiente verde->azul e decoracao."""
    subtitle_html = f"<p>{subtitle}</p>" if subtitle else ""
    badge_html = f'<span class="hero-badge">{badge}</span>' if badge else ""
    st.markdown(f"""
    <div class="hero-header">
        <div class="hero-accent"></div>
        <h1>{title}</h1>
        {subtitle_html}
        {badge_html}
    </div>
    """, unsafe_allow_html=True)


# === Empty State ===

def render_empty_state(message: str, icon: str = ""):
    """Renderiza um estado vazio estilizado."""
    icon_html = f'<div class="empty-icon">{icon}</div>' if icon else ""
    st.markdown(f"""
    <div class="empty-state">
        {icon_html}
        <p class="empty-message">{message}</p>
    </div>
    """, unsafe_allow_html=True)


# === Footer ===

def render_footer():
    """Renderiza footer branded Somus Capital."""
    year = datetime.now().year
    st.markdown(f"""
    <div class="somus-footer">
        <span class="footer-line"></span>
        <span class="footer-brand">Somus Capital</span>
        <span class="footer-separator">|</span>
        Investment HUB v2.1
        <span class="footer-separator">|</span>
        {year}
    </div>
    """, unsafe_allow_html=True)
