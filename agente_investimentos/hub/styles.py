"""CSS premium do HUB Somus Capital - Design System v2."""

from agente_investimentos.config import COR_VERDE_ESCURO, COR_AZUL

HUB_CSS = f"""
<style>
    /* ===================================================
       CSS Variables - Somus Capital Design System v2
       =================================================== */
    :root {{
        --somus-green: {COR_VERDE_ESCURO};
        --somus-blue: {COR_AZUL};
        --somus-gold: #C9A84C;
        --somus-dark: #003326;
        --somus-beige: #f7f7f2;
        --somus-gray-900: #212121;
        --somus-gray-700: #4a4a5a;
        --somus-gray-500: #828294;
        --somus-gray-400: #a0a0b0;
        --somus-gray-300: #d0d0d8;
        --somus-gray-200: #e2e8f0;
        --somus-gray-100: #f4f4f6;
        --somus-white: #ffffff;
        --somus-red: #c62828;
        --somus-orange: #e65100;

        --somus-shadow-xs: 0 1px 2px rgba(0,0,0,0.04);
        --somus-shadow-sm: 0 1px 3px rgba(0,0,0,0.06), 0 1px 2px rgba(0,0,0,0.04);
        --somus-shadow-md: 0 4px 8px rgba(0,0,0,0.06), 0 2px 4px rgba(0,0,0,0.04);
        --somus-shadow-lg: 0 10px 20px rgba(0,0,0,0.08), 0 4px 8px rgba(0,0,0,0.04);
        --somus-shadow-xl: 0 20px 40px rgba(0,0,0,0.10), 0 8px 16px rgba(0,0,0,0.04);

        --somus-radius-xs: 4px;
        --somus-radius-sm: 6px;
        --somus-radius: 10px;
        --somus-radius-lg: 14px;
        --somus-radius-xl: 20px;

        --somus-transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
        --somus-transition-fast: all 0.15s ease;
    }}

    /* ===================================================
       Top Logo Bar (canto superior esquerdo)
       =================================================== */
    .top-logo-bar {{
        display: flex;
        align-items: center;
        padding: 0 0 0.6rem 0;
        margin-bottom: 0.2rem;
    }}

    .top-logo {{
        height: 36px;
        width: auto;
        display: block;
        /* Logo branca -> verde Somus #004d33 via CSS filter */
        filter: brightness(0) saturate(100%) invert(20%) sepia(95%) saturate(600%) hue-rotate(130deg) brightness(70%);
    }}

    /* ===================================================
       Custom Scrollbar
       =================================================== */
    *::-webkit-scrollbar {{ width: 5px; height: 5px; }}
    *::-webkit-scrollbar-track {{ background: transparent; }}
    *::-webkit-scrollbar-thumb {{
        background: var(--somus-gray-300);
        border-radius: 10px;
    }}
    *::-webkit-scrollbar-thumb:hover {{
        background: var(--somus-green);
    }}

    /* ===================================================
       Global Enhancements
       =================================================== */
    .main .block-container {{
        padding-top: 1.5rem !important;
        max-width: 1200px;
    }}

    /* Subheaders com acento verde */
    .main h2 {{
        color: var(--somus-gray-900) !important;
        font-weight: 700 !important;
        font-size: 1.15rem !important;
        border-bottom: 2px solid var(--somus-green);
        padding-bottom: 0.5rem;
        margin-top: 0.5rem !important;
    }}

    /* Sub-header info text (usado no Dashboard) */
    .sub-header {{
        font-size: 0.88rem;
        color: var(--somus-gray-500);
        font-weight: 500;
        padding: 0.3rem 0;
        margin: 0;
    }}

    /* Dividers mais sutis */
    .main hr {{
        border-color: #edf0f3 !important;
        opacity: 0.7;
    }}

    /* ===================================================
       SIDEBAR - Interactive Collapsible (hover expand)
       =================================================== */

    /* Esconde controles de colapso nativos do Streamlit */
    [data-testid="stSidebarCollapsedControl"],
    section[data-testid="stSidebar"] > button {{
        display: none !important;
    }}

    /* --- Sidebar base: estreita (72px), expande ao hover --- */
    section[data-testid="stSidebar"] {{
        width: 72px !important;
        min-width: 72px !important;
        max-width: 72px !important;
        background: var(--somus-white) !important;
        border-right: 1px solid var(--somus-gray-200) !important;
        overflow: hidden !important;
        transition: width 0.3s cubic-bezier(0.4, 0, 0.2, 1),
                    min-width 0.3s cubic-bezier(0.4, 0, 0.2, 1),
                    max-width 0.3s cubic-bezier(0.4, 0, 0.2, 1),
                    box-shadow 0.3s ease !important;
    }}

    section[data-testid="stSidebar"]:hover {{
        width: 280px !important;
        min-width: 280px !important;
        max-width: 280px !important;
        box-shadow: 6px 0 30px rgba(0,0,0,0.12) !important;
    }}

    section[data-testid="stSidebar"] > div:first-child {{
        padding: 0 !important;
        height: 100% !important;
    }}

    /* Scrollable quando expandida */
    section[data-testid="stSidebar"]:hover > div:first-child {{
        overflow-y: auto !important;
        overflow-x: hidden !important;
    }}

    /* Sticky support para estado expandido */
    section[data-testid="stSidebar"]:hover [data-testid="stSidebarContent"] {{
        overflow: visible !important;
    }}
    section[data-testid="stSidebar"]:hover [data-testid="stVerticalBlockBorderWrapper"] {{
        overflow: visible !important;
    }}
    section[data-testid="stSidebar"]:hover [data-testid="stVerticalBlock"] {{
        overflow: visible !important;
    }}

    /* --- Brand Area: logo centralizada --- */
    .sidebar-brand-area {{
        position: sticky;
        top: 0;
        z-index: 999;
        background: linear-gradient(165deg, {COR_VERDE_ESCURO} 0%, var(--somus-dark) 100%);
        text-align: center;
        padding: 0.9rem 0.4rem;
        border-bottom: 3px solid var(--somus-gold);
        box-shadow: 0 4px 16px rgba(0, 51, 38, 0.25);
        transition: padding 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }}

    section[data-testid="stSidebar"]:hover .sidebar-brand-area {{
        padding: 1.4rem 1rem;
    }}

    /* Wrapper sticky */
    section[data-testid="stSidebar"] [data-testid="element-container"]:has(.sidebar-brand-area) {{
        position: sticky !important;
        top: 0 !important;
        z-index: 999 !important;
    }}
    section[data-testid="stSidebar"] [data-testid="stMarkdown"]:has(.sidebar-brand-area) {{
        position: sticky !important;
        top: 0 !important;
        z-index: 999 !important;
    }}

    .sidebar-brand-area .sidebar-logo {{
        width: 38px;
        height: auto;
        margin: 0 auto;
        display: block;
        transition: width 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        /* Logo branca -> verde Somus #004d33 */
        filter: brightness(0) saturate(100%) invert(20%) sepia(95%) saturate(600%) hue-rotate(130deg) brightness(70%);
    }}

    section[data-testid="stSidebar"]:hover .sidebar-brand-area .sidebar-logo {{
        width: 100px;
    }}

    /* --- Section Labels: invisivel colapsada, visivel expandida --- */
    .sidebar-section-label {{
        font-size: 0.63rem !important;
        font-weight: 700 !important;
        color: var(--somus-gray-400) !important;
        text-transform: uppercase !important;
        letter-spacing: 1.8px !important;
        padding: 0.8rem 1rem 0.3rem !important;
        margin: 0 !important;
        opacity: 0;
        white-space: nowrap;
        transition: opacity 0.1s ease;
    }}
    section[data-testid="stSidebar"]:hover .sidebar-section-label {{
        opacity: 1;
        transition: opacity 0.2s ease 0.12s;
    }}

    /* --- Sidebar Divider --- */
    .sidebar-divider {{
        border: none;
        border-top: 1px solid #edf0f3;
        margin: 0.5rem 0.5rem;
        opacity: 0;
        transition: opacity 0.1s ease;
    }}
    section[data-testid="stSidebar"]:hover .sidebar-divider {{
        opacity: 1;
        transition: opacity 0.2s ease 0.12s;
    }}

    /* --- Nav Radio Items --- */
    section[data-testid="stSidebar"] div[role="radiogroup"] {{
        gap: 2px !important;
        padding: 0.3rem 6px !important;
    }}
    section[data-testid="stSidebar"] div[role="radiogroup"] label {{
        padding: 9px 8px !important;
        border-radius: var(--somus-radius-sm) !important;
        transition: all 0.2s ease !important;
        margin-bottom: 1px !important;
        border-left: 3px solid transparent !important;
        white-space: nowrap !important;
        min-height: 38px !important;
        position: relative !important;
    }}
    section[data-testid="stSidebar"]:hover div[role="radiogroup"] label {{
        padding: 9px 14px !important;
    }}

    /* Texto dos itens: fade in/out */
    section[data-testid="stSidebar"] div[role="radiogroup"] label p {{
        font-size: 0.87rem !important;
        opacity: 0;
        white-space: nowrap !important;
        transition: opacity 0.1s ease;
    }}
    section[data-testid="stSidebar"]:hover div[role="radiogroup"] label p {{
        opacity: 1;
        transition: opacity 0.2s ease 0.15s;
    }}

    /* Hover no item */
    section[data-testid="stSidebar"] div[role="radiogroup"] label:hover {{
        background-color: #f0faf5 !important;
        border-left-color: var(--somus-green) !important;
    }}

    /* Item ativo - indicador verde sempre visivel */
    section[data-testid="stSidebar"] div[role="radiogroup"] label[data-baseweb="radio"][aria-checked="true"],
    section[data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked) {{
        background-color: #e6f3eb !important;
        border-left-color: var(--somus-green) !important;
    }}
    section[data-testid="stSidebar"]:hover div[role="radiogroup"] label[data-baseweb="radio"][aria-checked="true"] p,
    section[data-testid="stSidebar"]:hover div[role="radiogroup"] label:has(input:checked) p {{
        font-weight: 700 !important;
        color: var(--somus-green) !important;
    }}

    /* --- Sidebar Buttons: escondidos colapsada --- */
    section[data-testid="stSidebar"] .stButton {{
        opacity: 0;
        overflow: hidden;
        transition: opacity 0.1s ease;
        padding: 0 6px;
    }}
    section[data-testid="stSidebar"]:hover .stButton {{
        opacity: 1;
        transition: opacity 0.2s ease 0.12s;
    }}
    section[data-testid="stSidebar"] .stButton > button {{
        background: transparent !important;
        border: 1.5px solid var(--somus-gray-200) !important;
        color: var(--somus-gray-700) !important;
        font-size: 0.8rem !important;
        font-weight: 600 !important;
        border-radius: var(--somus-radius-sm) !important;
        transition: var(--somus-transition) !important;
        letter-spacing: 0.3px !important;
        white-space: nowrap !important;
    }}
    section[data-testid="stSidebar"] .stButton > button:hover {{
        background: #f0faf5 !important;
        border-color: var(--somus-green) !important;
        color: var(--somus-green) !important;
    }}

    /* --- Sidebar Footer: escondido colapsada --- */
    .sidebar-footer {{
        text-align: center;
        padding: 1.2rem 0.5rem 0.8rem;
        margin-top: 1.5rem;
        border-top: 1px solid #edf0f3;
        opacity: 0;
        transition: opacity 0.1s ease;
    }}
    section[data-testid="stSidebar"]:hover .sidebar-footer {{
        opacity: 1;
        transition: opacity 0.2s ease 0.12s;
    }}
    .sidebar-footer p {{
        margin: 0;
        font-size: 0.68rem;
        color: var(--somus-gray-400);
        letter-spacing: 0.3px;
        line-height: 1.7;
        white-space: nowrap;
    }}
    .sidebar-footer .footer-version {{
        display: inline-block;
        background: var(--somus-green);
        color: white;
        padding: 2px 10px;
        border-radius: 10px;
        font-size: 0.6rem;
        font-weight: 700;
        letter-spacing: 0.5px;
        margin-bottom: 4px;
    }}

    /* ===================================================
       Hero Header - Enhanced
       =================================================== */
    .hero-header {{
        background: linear-gradient(135deg, var(--somus-green) 0%, #006644 50%, var(--somus-blue) 100%);
        color: var(--somus-white);
        padding: 2.2rem 2.5rem;
        border-radius: var(--somus-radius-lg);
        margin-bottom: 1.8rem;
        box-shadow: var(--somus-shadow-lg);
        position: relative;
        overflow: hidden;
    }}
    .hero-header::before {{
        content: '';
        position: absolute;
        top: -60%;
        right: -15%;
        width: 350px;
        height: 350px;
        background: rgba(255,255,255,0.06);
        border-radius: 50%;
    }}
    .hero-header::after {{
        content: '';
        position: absolute;
        bottom: -40%;
        left: -8%;
        width: 250px;
        height: 250px;
        background: rgba(255,255,255,0.04);
        border-radius: 50%;
    }}
    .hero-header .hero-accent {{
        position: absolute;
        top: 0;
        right: 0;
        width: 120px;
        height: 100%;
        background: linear-gradient(180deg, rgba(255,255,255,0.08) 0%, transparent 100%);
        clip-path: polygon(30% 0%, 100% 0%, 100% 100%, 0% 100%);
    }}
    .hero-header h1 {{
        font-size: 1.8rem;
        font-weight: 700;
        margin: 0 0 0.3rem 0;
        position: relative;
        z-index: 1;
        letter-spacing: 0.3px;
    }}
    .hero-header p {{
        font-size: 0.95rem;
        opacity: 0.85;
        margin: 0;
        position: relative;
        z-index: 1;
        font-weight: 400;
    }}
    .hero-header .hero-badge {{
        display: inline-block;
        background: rgba(255,255,255,0.15);
        padding: 3px 14px;
        border-radius: 20px;
        font-size: 0.68rem;
        font-weight: 600;
        letter-spacing: 0.8px;
        margin-top: 0.8rem;
        position: relative;
        z-index: 1;
        text-transform: uppercase;
        border: 1px solid rgba(255,255,255,0.2);
    }}

    /* ===================================================
       KPI Cards Premium
       =================================================== */
    div[data-testid="stMetric"] {{
        background-color: var(--somus-white);
        border: 1px solid #edf0f3;
        border-left: 4px solid var(--somus-green);
        border-radius: var(--somus-radius);
        padding: 16px 20px;
        box-shadow: var(--somus-shadow-sm);
        transition: var(--somus-transition);
    }}
    div[data-testid="stMetric"]:hover {{
        box-shadow: var(--somus-shadow-md);
        transform: translateY(-2px);
        border-left-color: var(--somus-blue);
    }}
    div[data-testid="stMetric"] label {{
        color: var(--somus-gray-500) !important;
        font-size: 0.72rem !important;
        text-transform: uppercase;
        letter-spacing: 0.8px;
        font-weight: 700 !important;
    }}
    div[data-testid="stMetric"] [data-testid="stMetricValue"] {{
        color: var(--somus-gray-900) !important;
        font-weight: 700 !important;
        font-size: 1.4rem !important;
    }}

    /* ===================================================
       News Cards Premium
       =================================================== */
    .news-card {{
        background: var(--somus-white);
        border: 1px solid #edf0f3;
        border-left: 4px solid var(--somus-blue);
        border-radius: var(--somus-radius);
        padding: 16px 20px;
        margin-bottom: 12px;
        transition: var(--somus-transition);
        box-shadow: var(--somus-shadow-xs);
    }}
    .news-card:hover {{
        box-shadow: var(--somus-shadow-md);
        transform: translateX(4px);
        border-left-color: var(--somus-green);
    }}
    .news-card-title {{
        font-size: 0.95rem;
        font-weight: 600;
        color: var(--somus-gray-900);
        margin-bottom: 6px;
        line-height: 1.45;
    }}
    .news-card-title a {{
        color: var(--somus-gray-900);
        text-decoration: none;
        transition: color 0.2s;
    }}
    .news-card-title a:hover {{
        color: var(--somus-blue);
    }}
    .news-card-meta {{
        font-size: 0.78rem;
        color: var(--somus-gray-500);
        display: flex;
        align-items: center;
        gap: 6px;
        flex-wrap: wrap;
    }}

    /* ===================================================
       Badges (Categorias & Impacto)
       =================================================== */
    .badge {{
        display: inline-block;
        padding: 2px 10px;
        border-radius: 20px;
        font-size: 0.68rem;
        font-weight: 700;
        margin-right: 4px;
        letter-spacing: 0.5px;
        text-transform: uppercase;
    }}
    .badge-economia {{ background: #e8f4fd; color: #1565c0; }}
    .badge-política {{ background: #fce4ec; color: #c62828; }}
    .badge-mercado {{ background: #e8f5e9; color: #2e7d32; }}
    .badge-esportes {{ background: #fff3e0; color: #e65100; }}
    .badge-todas {{ background: #f3e5f5; color: #6a1b9a; }}
    .badge-positivo {{ background: #e8f5e9; color: #2e7d32; }}
    .badge-negativo {{ background: #ffebee; color: #c62828; }}
    .badge-neutro {{ background: #f0f0f0; color: #616161; }}

    /* ===================================================
       Tabs Premium
       =================================================== */
    .stTabs [data-baseweb="tab-list"] {{
        gap: 0px;
        border-bottom: 2px solid #edf0f3;
        background: transparent;
    }}
    .stTabs [data-baseweb="tab"] {{
        padding: 10px 22px;
        font-weight: 500;
        color: var(--somus-gray-500);
        border-bottom: 3px solid transparent;
        transition: var(--somus-transition);
        font-size: 0.87rem;
    }}
    .stTabs [data-baseweb="tab"]:hover {{
        color: var(--somus-green);
        background: #f0faf5;
    }}
    .stTabs [aria-selected="true"] {{
        color: var(--somus-green) !important;
        border-bottom: 3px solid var(--somus-green) !important;
        font-weight: 700 !important;
    }}

    /* ===================================================
       Buttons Premium (Main area only)
       =================================================== */
    .main .stButton > button[kind="primary"],
    .main .stButton > button[data-testid="stBaseButton-primary"] {{
        background: linear-gradient(135deg, var(--somus-green) 0%, #006644 100%) !important;
        color: var(--somus-white) !important;
        border: none !important;
        border-radius: var(--somus-radius-sm) !important;
        font-weight: 700 !important;
        letter-spacing: 0.5px !important;
        box-shadow: 0 2px 8px rgba(0,77,51,0.25) !important;
        transition: var(--somus-transition) !important;
        padding: 10px 20px !important;
    }}
    .main .stButton > button[kind="primary"]:hover,
    .main .stButton > button[data-testid="stBaseButton-primary"]:hover {{
        box-shadow: 0 4px 16px rgba(0,77,51,0.35) !important;
        transform: translateY(-1px) !important;
    }}
    .main .stButton > button[kind="secondary"],
    .main .stButton > button[data-testid="stBaseButton-secondary"] {{
        border: 1.5px solid var(--somus-green) !important;
        color: var(--somus-green) !important;
        border-radius: var(--somus-radius-sm) !important;
        font-weight: 600 !important;
        transition: var(--somus-transition) !important;
        background: transparent !important;
    }}
    .main .stButton > button[kind="secondary"]:hover,
    .main .stButton > button[data-testid="stBaseButton-secondary"]:hover {{
        background-color: rgba(0,77,51,0.06) !important;
    }}

    /* ===================================================
       Form Inputs Enhanced
       =================================================== */
    .stTextInput > div > div > input,
    .stNumberInput > div > div > input,
    .stTextArea > div > div > textarea {{
        border: 1.5px solid var(--somus-gray-200) !important;
        border-radius: var(--somus-radius-sm) !important;
        transition: var(--somus-transition) !important;
        font-size: 0.9rem !important;
    }}
    .stTextInput > div > div > input:focus,
    .stNumberInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {{
        border-color: var(--somus-green) !important;
        box-shadow: 0 0 0 2px rgba(0,77,51,0.1) !important;
    }}

    /* Selectbox */
    .stSelectbox > div > div {{
        border-radius: var(--somus-radius-sm) !important;
        transition: var(--somus-transition) !important;
    }}

    /* Multiselect */
    .stMultiSelect > div > div {{
        border-radius: var(--somus-radius-sm) !important;
    }}

    /* Date Input */
    .stDateInput > div > div {{
        border-radius: var(--somus-radius-sm) !important;
    }}

    /* File Uploader */
    .stFileUploader > div {{
        border: 2px dashed #d0d5dd !important;
        border-radius: var(--somus-radius) !important;
        transition: var(--somus-transition) !important;
    }}
    .stFileUploader > div:hover {{
        border-color: var(--somus-green) !important;
        background: #f0faf5 !important;
    }}

    /* ===================================================
       Progress Bar
       =================================================== */
    .stProgress > div > div > div > div {{
        background: linear-gradient(90deg, var(--somus-green), var(--somus-blue)) !important;
        border-radius: 10px !important;
    }}

    /* ===================================================
       Impact Analysis Cards
       =================================================== */
    .impact-card {{
        background: var(--somus-white);
        border: 1px solid #edf0f3;
        border-radius: var(--somus-radius-lg);
        margin-bottom: 1.2rem;
        box-shadow: var(--somus-shadow-sm);
        overflow: hidden;
        transition: var(--somus-transition);
    }}
    .impact-card:hover {{
        box-shadow: var(--somus-shadow-md);
        transform: translateY(-1px);
    }}
    .impact-card-header {{
        padding: 1rem 1.5rem;
        display: flex;
        align-items: center;
        gap: 12px;
    }}
    .impact-card-icon {{
        font-size: 1.4rem;
        flex-shrink: 0;
        width: 42px;
        height: 42px;
        display: flex;
        align-items: center;
        justify-content: center;
        border-radius: 10px;
    }}
    .impact-card-header h3 {{
        margin: 0;
        font-size: 1rem;
        font-weight: 700;
        letter-spacing: 0.3px;
    }}
    .impact-card-body {{
        padding: 0 1.5rem 1.2rem;
        color: var(--somus-gray-700);
        font-size: 0.9rem;
        line-height: 1.7;
    }}
    .impact-card-body ul {{
        padding-left: 1.2rem;
        margin: 0.5rem 0;
    }}
    .impact-card-body li {{
        margin-bottom: 0.4rem;
    }}
    .impact-card-body strong {{
        color: var(--somus-gray-900);
    }}

    /* Panorama - azul */
    .impact-card.panorama .impact-card-header {{
        background: linear-gradient(135deg, #e3f2fd 0%, #f0f7ff 100%);
        border-bottom: 2px solid #1565c0;
    }}
    .impact-card.panorama .impact-card-header h3 {{ color: #1565c0; }}
    .impact-card.panorama .impact-card-icon {{ background: #1565c0; color: white; }}

    /* Risco - vermelho */
    .impact-card.risco .impact-card-header {{
        background: linear-gradient(135deg, #ffebee 0%, #fff5f5 100%);
        border-bottom: 2px solid #c62828;
    }}
    .impact-card.risco .impact-card-header h3 {{ color: #c62828; }}
    .impact-card.risco .impact-card-icon {{ background: #c62828; color: white; }}

    /* Favorecido - verde */
    .impact-card.favorecido .impact-card-header {{
        background: linear-gradient(135deg, #e8f5e9 0%, #f1f8f2 100%);
        border-bottom: 2px solid #2e7d32;
    }}
    .impact-card.favorecido .impact-card-header h3 {{ color: #2e7d32; }}
    .impact-card.favorecido .impact-card-icon {{ background: #2e7d32; color: white; }}

    /* Ações - dourado */
    .impact-card.ações .impact-card-header {{
        background: linear-gradient(135deg, #fff8e1 0%, #fffdf5 100%);
        border-bottom: 2px solid #f57f17;
    }}
    .impact-card.ações .impact-card-header h3 {{ color: #e65100; }}
    .impact-card.ações .impact-card-icon {{ background: #f57f17; color: white; }}

    /* Resumo - verde Somus gradient */
    .impact-card.resumo .impact-card-header {{
        background: linear-gradient(135deg, var(--somus-green) 0%, var(--somus-blue) 100%);
        border-bottom: none;
    }}
    .impact-card.resumo .impact-card-header h3 {{ color: var(--somus-white); }}
    .impact-card.resumo .impact-card-icon {{ background: rgba(255,255,255,0.2); color: white; }}
    .impact-card.resumo .impact-card-body {{
        background: #f8faf9;
        border-left: 4px solid var(--somus-green);
        margin: 0 1rem 1rem;
        padding: 1rem 1.2rem;
        border-radius: 0 var(--somus-radius-sm) var(--somus-radius-sm) 0;
    }}

    /* ===================================================
       News Filter Bar
       =================================================== */
    .news-filter-bar {{
        background: var(--somus-white);
        border: 1px solid #edf0f3;
        border-radius: var(--somus-radius);
        padding: 1rem 1.2rem;
        margin-bottom: 1rem;
        box-shadow: var(--somus-shadow-xs);
    }}
    .news-stats {{
        display: inline-block;
        background: #f0faf5;
        padding: 4px 14px;
        border-radius: 20px;
        font-size: 0.78rem;
        color: var(--somus-green);
        font-weight: 700;
        border: 1px solid rgba(0,77,51,0.1);
    }}

    /* ===================================================
       Impact Section (simple)
       =================================================== */
    .impact-section {{
        background: var(--somus-white);
        border-left: 4px solid var(--somus-green);
        padding: 14px 18px;
        margin-bottom: 14px;
        border-radius: 0 var(--somus-radius) var(--somus-radius) 0;
        box-shadow: var(--somus-shadow-sm);
    }}
    .impact-section h4 {{
        color: var(--somus-green);
        margin-bottom: 8px;
        font-weight: 700;
    }}

    /* ===================================================
       Migration Card
       =================================================== */
    .migration-card {{
        background: var(--somus-white);
        border: 1px solid #edf0f3;
        border-radius: var(--somus-radius);
        padding: 18px;
        margin-bottom: 12px;
        box-shadow: var(--somus-shadow-sm);
        transition: var(--somus-transition);
    }}
    .migration-card:hover {{
        box-shadow: var(--somus-shadow-md);
    }}

    /* ===================================================
       Empty State
       =================================================== */
    .empty-state {{
        text-align: center;
        padding: 3rem 2rem;
        border: 2px dashed #d0d5dd;
        border-radius: var(--somus-radius-lg);
        background: #fafaf8;
        margin: 1.5rem 0;
    }}
    .empty-state .empty-icon {{
        font-size: 2.5rem;
        margin-bottom: 0.8rem;
        opacity: 0.5;
    }}
    .empty-state .empty-message {{
        color: var(--somus-gray-500);
        font-size: 0.95rem;
        margin: 0;
        font-weight: 500;
    }}

    /* ===================================================
       Footer Branded
       =================================================== */
    .somus-footer {{
        text-align: center;
        padding: 1.5rem 0 0.5rem;
        margin-top: 3rem;
        border-top: 2px solid #edf0f3;
        color: var(--somus-gray-500);
        font-size: 0.75rem;
    }}
    .somus-footer .footer-line {{
        display: block;
        width: 40px;
        height: 3px;
        background: linear-gradient(90deg, var(--somus-green), var(--somus-gold));
        margin: 0 auto 10px;
        border-radius: 2px;
    }}
    .somus-footer .footer-brand {{
        color: var(--somus-green);
        font-weight: 800;
        letter-spacing: 1.5px;
        text-transform: uppercase;
        font-size: 0.82rem;
    }}
    .somus-footer .footer-separator {{
        margin: 0 10px;
        color: #d0d5dd;
    }}

    /* ===================================================
       Expander Premium
       =================================================== */
    .streamlit-expanderHeader {{
        font-weight: 600 !important;
        color: var(--somus-gray-900) !important;
        background: #fafafa !important;
        border-radius: var(--somus-radius-sm) !important;
    }}

    /* ===================================================
       Data Tables / Dataframes
       =================================================== */
    .stDataFrame {{
        border-radius: var(--somus-radius) !important;
        overflow: hidden;
        box-shadow: var(--somus-shadow-sm) !important;
    }}

    /* ===================================================
       Download Buttons
       =================================================== */
    .stDownloadButton > button {{
        border: 1.5px solid var(--somus-blue) !important;
        color: var(--somus-blue) !important;
        border-radius: var(--somus-radius-sm) !important;
        font-weight: 600 !important;
        transition: var(--somus-transition) !important;
        background: transparent !important;
    }}
    .stDownloadButton > button:hover {{
        background-color: rgba(24,99,220,0.06) !important;
        box-shadow: var(--somus-shadow-sm) !important;
        transform: translateY(-1px) !important;
    }}

    /* ===================================================
       Alerts Enhanced
       =================================================== */
    .stAlert {{
        border-radius: var(--somus-radius-sm) !important;
    }}

    /* ===================================================
       Change Registry Specific
       =================================================== */
    .change-kpi {{
        background: var(--somus-white);
        border: 1px solid #edf0f3;
        border-radius: var(--somus-radius);
        padding: 1.2rem;
        text-align: center;
        box-shadow: var(--somus-shadow-sm);
        transition: var(--somus-transition);
    }}
    .change-kpi:hover {{
        box-shadow: var(--somus-shadow-md);
        transform: translateY(-2px);
    }}
    .change-kpi .kpi-value {{
        font-size: 1.8rem;
        font-weight: 800;
        color: var(--somus-green);
        margin: 0;
    }}
    .change-kpi .kpi-label {{
        font-size: 0.72rem;
        color: var(--somus-gray-500);
        text-transform: uppercase;
        letter-spacing: 0.8px;
        margin: 4px 0 0;
        font-weight: 700;
    }}

    .change-action-compra {{ border-left: 4px solid #2e7d32 !important; }}
    .change-action-venda {{ border-left: 4px solid #c62828 !important; }}
    .change-action-aumento {{ border-left: 4px solid var(--somus-blue) !important; }}
    .change-action-redução {{ border-left: 4px solid #e65100 !important; }}
    .change-action-migração {{ border-left: 4px solid var(--somus-gold) !important; }}

    /* ===================================================
       Daily Summary Cards
       =================================================== */
    .daily-summary-container {{
        margin-bottom: 1.5rem;
    }}
    .daily-summary-card {{
        background: var(--somus-white);
        border: 1px solid #edf0f3;
        border-radius: var(--somus-radius-lg);
        overflow: hidden;
        box-shadow: var(--somus-shadow-sm);
        transition: var(--somus-transition);
        height: 100%;
    }}
    .daily-summary-card:hover {{
        box-shadow: var(--somus-shadow-md);
        transform: translateY(-2px);
    }}
    .daily-summary-card-header {{
        padding: 0.8rem 1.2rem;
        display: flex;
        align-items: center;
        gap: 10px;
    }}
    .daily-summary-card-icon {{
        font-size: 1.2rem;
        width: 36px;
        height: 36px;
        display: flex;
        align-items: center;
        justify-content: center;
        border-radius: 8px;
        flex-shrink: 0;
    }}
    .daily-summary-card-header h4 {{
        margin: 0;
        font-size: 0.9rem;
        font-weight: 700;
        letter-spacing: 0.3px;
    }}
    .daily-summary-card-body {{
        padding: 0 1.2rem 1rem;
        color: var(--somus-gray-700);
        font-size: 0.85rem;
        line-height: 1.65;
    }}

    /* Geopolítica - azul escuro */
    .daily-summary-card.geopolítica .daily-summary-card-header {{
        background: linear-gradient(135deg, #e3f2fd 0%, #f0f7ff 100%);
        border-bottom: 2px solid #1565c0;
    }}
    .daily-summary-card.geopolítica .daily-summary-card-header h4 {{ color: #1565c0; }}
    .daily-summary-card.geopolítica .daily-summary-card-icon {{ background: #1565c0; color: white; }}

    /* IA - roxo */
    .daily-summary-card.ai .daily-summary-card-header {{
        background: linear-gradient(135deg, #f3e5f5 0%, #faf5fc 100%);
        border-bottom: 2px solid #7b1fa2;
    }}
    .daily-summary-card.ai .daily-summary-card-header h4 {{ color: #7b1fa2; }}
    .daily-summary-card.ai .daily-summary-card-icon {{ background: #7b1fa2; color: white; }}

    /* Economia - verde Somus */
    .daily-summary-card.economia .daily-summary-card-header {{
        background: linear-gradient(135deg, #e8f5e9 0%, #f1f8f2 100%);
        border-bottom: 2px solid var(--somus-green);
    }}
    .daily-summary-card.economia .daily-summary-card-header h4 {{ color: var(--somus-green); }}
    .daily-summary-card.economia .daily-summary-card-icon {{ background: var(--somus-green); color: white; }}

    /* ===================================================
       Divider
       =================================================== */
    .divider {{
        border-top: 1px solid #edf0f3;
        margin: 1rem 0;
    }}

    /* ===================================================
       Login Screen
       =================================================== */
    .login-container {{
        display: flex;
        justify-content: center;
        padding-top: 6vh;
    }}

    .login-card {{
        text-align: center;
        padding: 2.5rem 3rem 1.5rem;
    }}

    .login-logo {{
        height: 72px;
        width: auto;
        margin-bottom: 1.5rem;
        /* Logo branca -> verde Somus #004d33 */
        filter: brightness(0) saturate(100%) invert(20%) sepia(95%) saturate(600%) hue-rotate(130deg) brightness(70%);
    }}

    .login-title {{
        font-size: 1.6rem !important;
        font-weight: 700 !important;
        color: var(--somus-green) !important;
        margin: 0 !important;
        padding: 0 !important;
        border: none !important;
    }}

    .login-subtitle {{
        font-size: 0.88rem;
        color: var(--somus-gray-500);
        margin-top: 0.3rem;
        letter-spacing: 0.5px;
    }}
</style>
"""


def inject_css():
    """Injeta o CSS customizado na página Streamlit."""
    import streamlit as st
    st.markdown(HUB_CSS, unsafe_allow_html=True)
