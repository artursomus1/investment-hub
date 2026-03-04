"""
Investment HUB - Somus Capital
===============================
Executa com: streamlit run app.py
"""

import base64
import os
import sys
from pathlib import Path
from urllib.parse import quote

# Garante que o diretório do projeto está no path
_PROJECT_DIR = Path(__file__).resolve().parent
if str(_PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(_PROJECT_DIR))

import streamlit as st

from agente_investimentos.config import COR_VERDE_ESCURO, LOGO_PATH
from agente_investimentos.dashboard.session_persistence import (
    ensure_session_state, load_session_meta, cleanup_old_session,
)
from agente_investimentos.dashboard.run_history import cleanup_old_runs
from agente_investimentos.dashboard.change_registry import cleanup_old_changes
from agente_investimentos.hub.styles import inject_css

# Carrega .env se dotenv disponivel
try:
    from dotenv import load_dotenv
    load_dotenv(_PROJECT_DIR / ".env")
except ImportError:
    pass

# Senha de acesso (definida no .env ou st.secrets)
_HUB_PASSWORD = os.getenv("HUB_PASSWORD") or st.secrets.get("HUB_PASSWORD", "")

# ============================================================
# Configuração da página
# ============================================================
st.set_page_config(
    page_title="Investment HUB - Somus Capital",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Injeta CSS customizado
inject_css()

# Viewport meta tag para renderizacao mobile correta
st.markdown(
    '<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">',
    unsafe_allow_html=True,
)


# ============================================================
# Tela de Login (bloqueia acesso sem senha)
# ============================================================
def _show_login():
    """Exibe tela de login e retorna True se autenticado."""
    # Esconde a sidebar na tela de login
    st.markdown(
        "<style>"
        "section[data-testid='stSidebar'] { display: none !important; }"
        "[data-testid='stSidebarCollapsedControl'] { display: none !important; }"
        "</style>",
        unsafe_allow_html=True,
    )

    # Logo
    logo_b64 = ""
    if LOGO_PATH.exists():
        logo_b64 = base64.b64encode(LOGO_PATH.read_bytes()).decode()

    logo_html = (
        f'<img src="data:image/png;base64,{logo_b64}" '
        f'class="login-logo" alt="Somus Capital" />'
        if logo_b64 else ""
    )

    st.markdown(
        f'<div class="login-container">'
        f'<div class="login-card">'
        f'{logo_html}'
        f'<h2 class="login-title">Investment HUB</h2>'
        f'<p class="login-subtitle">Acesso restrito</p>'
        f'</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # Campo de senha centralizado
    col_l, col_c, col_r = st.columns([1, 1.5, 1])
    with col_c:
        senha = st.text_input(
            "Senha de acesso",
            type="password",
            placeholder="Digite a senha",
            label_visibility="collapsed",
        )
        btn = st.button("Entrar", type="primary", use_container_width=True)

        if btn:
            if senha == _HUB_PASSWORD:
                st.session_state["authenticated"] = True
                st.rerun()
            else:
                st.error("Senha incorreta.")

    st.markdown(
        '<p style="text-align:center;color:#828294;font-size:0.75rem;margin-top:2rem;">'
        'Somus Capital &middot; Investment HUB v2.1'
        '</p>',
        unsafe_allow_html=True,
    )


# Gate de autenticacao
if not st.session_state.get("authenticated", False):
    _show_login()
    st.stop()

# ============================================================
# Startup: auto-cleanup + carregar sessao persistida
# ============================================================
if not st.session_state.get("_cleanup_done", False):
    cleanup_old_session(3)
    cleanup_old_runs(3)
    cleanup_old_changes(3)
    st.session_state["_cleanup_done"] = True

ensure_session_state()

# ============================================================
# Logo superior esquerdo (visível para todos os visitantes)
# ============================================================
_main_logo_b64 = ""
if LOGO_PATH.exists():
    _main_logo_b64 = base64.b64encode(LOGO_PATH.read_bytes()).decode()

if _main_logo_b64:
    st.markdown(
        f'<div class="top-logo-bar">'
        f'<img src="data:image/png;base64,{_main_logo_b64}" alt="Somus Capital" class="top-logo" />'
        f'</div>',
        unsafe_allow_html=True,
    )

# ============================================================
# Páginas
# ============================================================
PAGES = {
    "Notícias": "page_news",
    "Carteira": "page_portfolio",
    "Dashboard": "page_dashboard",
    "Impacto": "page_news_impact",
    "Migração": "page_migration",
    "Consolidador": "page_consolidador",
    "Registro de Mudanças": "page_changes",
    "Histórico": "page_history",
}


# ============================================================
# Dialog de reporte de erro (definido fora do sidebar)
# ============================================================
@st.dialog("Reportar Erro / Sugestão")
def _report_dialog():
    report_type = st.selectbox("Tipo", ["Erro / Bug", "Melhoria / Sugestão", "Outro"])
    page_ctx = st.selectbox("Página", list(PAGES.keys()), index=0)
    description = st.text_area(
        "Descreva o problema ou sugestão",
        placeholder="Detalhe o que aconteceu ou o que gostaria de melhorar...",
        height=150,
    )
    if st.button("Enviar", type="primary", use_container_width=True):
        if not description.strip():
            st.error("Preencha a descrição.")
        else:
            subject = quote(f"[Investment HUB] {report_type} - {page_ctx}")
            body = quote(
                f"Tipo: {report_type}\n"
                f"Página: {page_ctx}\n\n"
                f"Descrição:\n{description}\n\n"
                f"---\nEnviado via Investment HUB v2.1"
            )
            mailto = f"mailto:artur.brito@somuscapital.com.br?subject={subject}&body={body}"
            st.markdown(
                f'<a href="{mailto}" target="_blank" '
                f'style="display:inline-block;width:100%;text-align:center;'
                f'padding:10px;background:#004d33;color:white;border-radius:6px;'
                f'text-decoration:none;font-weight:600;">'
                f'Abrir no Email</a>',
                unsafe_allow_html=True,
            )
            st.success("Clique no botao acima para abrir seu cliente de email com o relato preenchido.")


# ============================================================
# Dialog de compartilhamento
# ============================================================
def _get_app_url() -> str:
    """Retorna a URL publica do app (Cloud ou tunnel)."""
    # 1. Streamlit Cloud: monta a partir de headers/context
    _is_cloud = "STREAMLIT_SHARING_MODE" in os.environ or "HOSTNAME" in os.environ
    if _is_cloud:
        try:
            headers = st.context.headers
            host = headers.get("Host", "")
            if host:
                return f"https://{host}"
        except Exception:
            pass

    # 2. Tunnel local (launch_public.py salva em .tunnel_url)
    _tunnel_file = _PROJECT_DIR / ".tunnel_url"
    if _tunnel_file.exists():
        url = _tunnel_file.read_text(encoding="utf-8").strip()
        if url:
            return url

    return ""


@st.dialog("Compartilhar Link")
def _share_dialog():
    public_url = _get_app_url()

    if public_url:
        st.markdown(
            '<p style="color:#828294;font-size:0.85rem;margin-bottom:0.8rem;">'
            'Envie este link para qualquer pessoa acessar o HUB:</p>',
            unsafe_allow_html=True,
        )
        st.code(public_url, language=None)
        st.info("O app esta online 24/7. Basta compartilhar o link acima.")
    else:
        st.warning("Nenhum link publico ativo. No Streamlit Cloud o link aparece automaticamente. "
                    "Localmente, inicie com `python launch_public.py`.")

    st.markdown(
        '<p style="font-size:0.75rem;color:#828294;margin-top:0.5rem;">'
        'Senha de acesso: solicite ao administrador</p>',
        unsafe_allow_html=True,
    )


# ============================================================
# Sidebar - Navegação
# ============================================================
with st.sidebar:
    # Logo + Brand em bloco único (sticky via CSS)
    _logo_b64 = ""
    if LOGO_PATH.exists():
        _logo_b64 = base64.b64encode(LOGO_PATH.read_bytes()).decode()
    _logo_img = (
        f'<img src="data:image/png;base64,{_logo_b64}" '
        f'class="sidebar-logo" alt="Somus Capital" />'
        if _logo_b64 else ""
    )

    st.markdown(
        f'<div class="sidebar-brand-area">'
        f'{_logo_img}'
        f'</div>',
        unsafe_allow_html=True,
    )

    # Navegação
    st.markdown('<p class="sidebar-section-label">Menu</p>', unsafe_allow_html=True)

    selected_page = st.radio(
        "Navegação",
        options=list(PAGES.keys()),
        index=0,
        label_visibility="collapsed",
    )

    st.markdown('<div class="sidebar-divider"></div>', unsafe_allow_html=True)
    st.markdown('<p class="sidebar-section-label">Ações Rápidas</p>', unsafe_allow_html=True)

    # Botao de reiniciar HUB (recarrega código atualizado)
    if st.button("🔄 Reiniciar HUB", use_container_width=True, type="primary",
                  help="Reinicia o HUB aplicando alterações de código"):
        st.cache_data.clear()
        st.cache_resource.clear()
        # Remove módulos do projeto do cache para forçar re-import
        _mods_to_remove = [
            k for k in sys.modules
            if k.startswith("agente_investimentos")
        ]
        for _mod in _mods_to_remove:
            del sys.modules[_mod]
        st.rerun()

    # Botao de atualizar dados
    if st.button("Atualizar Dados", use_container_width=True,
                  help="Recarrega notícias frescas (ignora cache)"):
        st.session_state["force_refresh_news"] = True
        st.rerun()

    # Botao compartilhar link
    if st.button("Compartilhar Link", use_container_width=True,
                  help="Copie o link publico para compartilhar"):
        _share_dialog()

    # Botao reportar erro
    if st.button("Reportar Erro", use_container_width=True,
                  help="Reporte um bug ou envie uma sugestão"):
        _report_dialog()

    # Carteira Ativa
    _meta = load_session_meta()
    if _meta and _meta.get("client_code"):
        try:
            from datetime import datetime as _dt
            _ts = _dt.fromisoformat(_meta["timestamp"])
            _ts_fmt = _ts.strftime("%d/%m %H:%M")
        except Exception:
            _ts_fmt = ""
        _patrimonio = _meta.get("total_bruto", 0)
        _pat_fmt = f"R$ {_patrimonio:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        st.markdown(
            '<div class="sidebar-divider"></div>'
            '<p class="sidebar-section-label">Carteira Ativa</p>',
            unsafe_allow_html=True,
        )
        st.markdown(
            f'<div style="background:#0a1929;border:1px solid #1a3a5c;border-radius:8px;'
            f'padding:12px;margin-bottom:12px;">'
            f'<p style="color:#90caf9;font-size:0.8rem;margin:0 0 4px 0;">Cliente</p>'
            f'<p style="color:white;font-weight:700;font-size:1rem;margin:0 0 8px 0;">{_meta["client_code"]}</p>'
            f'<p style="color:#90caf9;font-size:0.8rem;margin:0 0 2px 0;">'
            f'{_meta.get("num_ativos", 0)} ativos &middot; {_pat_fmt}</p>'
            f'<p style="color:#828294;font-size:0.7rem;margin:4px 0 0 0;">'
            f'Analisada em {_ts_fmt}</p>'
            f'</div>',
            unsafe_allow_html=True,
        )

    # Footer da sidebar
    st.markdown(
        '<div class="sidebar-footer">'
        '<span class="footer-version">v2.1</span>'
        '<p>Investment HUB</p>'
        '<p>Somus Capital</p>'
        '</div>',
        unsafe_allow_html=True,
    )

# ============================================================
# Roteamento - lazy import
# ============================================================
page_module = PAGES[selected_page]

if page_module == "page_news":
    from agente_investimentos.hub.page_news import render
elif page_module == "page_portfolio":
    from agente_investimentos.hub.page_portfolio import render
elif page_module == "page_dashboard":
    from agente_investimentos.hub.page_dashboard import render
elif page_module == "page_news_impact":
    from agente_investimentos.hub.page_news_impact import render
elif page_module == "page_migration":
    from agente_investimentos.hub.page_migration import render
elif page_module == "page_consolidador":
    from agente_investimentos.hub.page_consolidador import render
elif page_module == "page_changes":
    from agente_investimentos.hub.page_changes import render
elif page_module == "page_history":
    from agente_investimentos.hub.page_history import render

render()
