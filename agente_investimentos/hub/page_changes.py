"""Página Registro de Mudanças do HUB."""

import streamlit as st
from datetime import date, datetime

from agente_investimentos.dashboard.change_registry import (
    AÇÕES_VALIDAS,
    save_change,
    load_all_changes,
    filter_changes,
    get_change_metrics,
    delete_change,
)
from agente_investimentos.hub.components import (
    render_hero_header,
    render_empty_state,
    render_footer,
    format_brl,
)


def render():
    """Renderiza a página de registro de mudanças."""
    render_hero_header(
        "Registro de Mudanças",
        "Registre e acompanhe todas as movimentações nas carteiras dos clientes",
    )

    tab_novo, tab_histórico = st.tabs(["Novo Registro", "Histórico"])

    with tab_novo:
        _render_form()

    with tab_histórico:
        _render_history()

    render_footer()


def _render_form():
    """Formulario para novo registro de mudanca."""
    # Auto-fill do cliente se houver carteira carregada
    result = st.session_state.get("last_result")
    default_client = ""
    if result and result.get("portfolio"):
        default_client = result["portfolio"].client_code

    with st.form("change_form", clear_on_submit=True):
        col1, col2 = st.columns(2)

        with col1:
            data_mudanca = st.date_input(
                "Data da Mudanca",
                value=date.today(),
                format="DD/MM/YYYY",
            )
            client_code = st.text_input(
                "Código do Cliente",
                value=default_client,
                placeholder="Ex: ABC123",
            )
            ticker = st.text_input(
                "Ticker / Ativo",
                placeholder="Ex: PETR4, HGLG11, CDB BANCO X",
            )

        with col2:
            acao = st.selectbox("Tipo de Acao", options=AÇÕES_VALIDAS)
            quantidade = st.number_input("Quantidade", min_value=0.0, step=1.0, format="%.2f")
            valor = st.number_input("Valor Total (R$)", min_value=0.0, step=100.0, format="%.2f")

        motivacao = st.text_area(
            "Motivacao / Justificativa",
            placeholder="Descreva o motivo da movimentacao...",
            height=100,
        )
        recomendacao_ref = st.text_input(
            "Referencia de Recomendacao (opcional)",
            placeholder="Ex: Recomendacao do relatório de 15/02/2026",
        )

        submitted = st.form_submit_button("Registrar Mudanca", type="primary", use_container_width=True)

    if submitted:
        # Validacao
        errors = []
        if not client_code.strip():
            errors.append("Código do Cliente e obrigatorio.")
        if not ticker.strip():
            errors.append("Ticker / Ativo e obrigatorio.")
        if quantidade <= 0:
            errors.append("Quantidade deve ser maior que zero.")
        if valor <= 0:
            errors.append("Valor deve ser maior que zero.")

        if errors:
            for e in errors:
                st.error(e)
        else:
            record = save_change(
                data_mudanca=data_mudanca.strftime("%Y-%m-%d"),
                client_code=client_code,
                ticker=ticker,
                acao=acao,
                quantidade=quantidade,
                valor=valor,
                motivacao=motivacao,
                recomendacao_ref=recomendacao_ref,
            )
            st.success(
                f"Mudanca registrada com sucesso! "
                f"ID: {record.change_id} | {record.acao} {record.ticker} para {record.client_code}"
            )


def _render_history():
    """Histórico de mudanças com filtros e KPIs."""
    all_records = load_all_changes()

    if not all_records:
        render_empty_state("Nenhuma mudanca registrada ainda. Use a aba 'Novo Registro' para comecar.")
        return

    # Filtros
    st.markdown("**Filtros**")
    fc1, fc2, fc3, fc4 = st.columns(4)

    with fc1:
        clients = sorted(set(r.client_code for r in all_records))
        filter_client = st.selectbox("Cliente", options=["Todos"] + clients)

    with fc2:
        tickers = sorted(set(r.ticker for r in all_records))
        filter_ticker = st.selectbox("Ticker", options=["Todos"] + tickers)

    with fc3:
        filter_acao = st.selectbox("Acao", options=["Todas"] + AÇÕES_VALIDAS)

    with fc4:
        date_range = st.date_input(
            "Periodo",
            value=[],
            format="DD/MM/YYYY",
        )

    # Aplica filtros
    filtered = filter_changes(
        all_records,
        client_code=filter_client if filter_client != "Todos" else None,
        ticker=filter_ticker if filter_ticker != "Todos" else None,
        acao=filter_acao if filter_acao != "Todas" else None,
        data_inicio=date_range[0].strftime("%Y-%m-%d") if len(date_range) >= 1 else None,
        data_fim=date_range[1].strftime("%Y-%m-%d") if len(date_range) >= 2 else None,
    )

    # KPIs
    metrics = get_change_metrics(filtered)
    st.divider()

    k1, k2, k3, k4, k5 = st.columns(5)
    k1.markdown(f"""
    <div class="change-kpi">
        <p class="kpi-value">{metrics['total']}</p>
        <p class="kpi-label">Total</p>
    </div>
    """, unsafe_allow_html=True)
    k2.markdown(f"""
    <div class="change-kpi change-action-compra">
        <p class="kpi-value">{metrics['compras']}</p>
        <p class="kpi-label">Compras</p>
    </div>
    """, unsafe_allow_html=True)
    k3.markdown(f"""
    <div class="change-kpi change-action-venda">
        <p class="kpi-value">{metrics['vendas']}</p>
        <p class="kpi-label">Vendas</p>
    </div>
    """, unsafe_allow_html=True)
    k4.markdown(f"""
    <div class="change-kpi change-action-migração">
        <p class="kpi-value">{metrics['migrações']}</p>
        <p class="kpi-label">Migrações</p>
    </div>
    """, unsafe_allow_html=True)
    k5.markdown(f"""
    <div class="change-kpi">
        <p class="kpi-value">{format_brl(metrics['valor_total'])}</p>
        <p class="kpi-label">Valor Total</p>
    </div>
    """, unsafe_allow_html=True)

    # Tabela de registros
    st.divider()
    st.markdown(f"**{len(filtered)} registro(s) encontrado(s)**")

    for rec in filtered:
        acao_lower = rec.acao.lower()
        acao_class = f"change-action-{acao_lower}" if acao_lower in ("compra", "venda", "aumento", "redução", "migração") else ""

        with st.container():
            cols = st.columns([1.2, 1.2, 1, 1.2, 1.5, 2, 0.6])
            cols[0].markdown(f"**{rec.data_mudanca}**")
            cols[1].markdown(f"`{rec.client_code}`")
            cols[2].markdown(f"**{rec.ticker}**")
            cols[3].markdown(f"**{rec.acao}**")
            cols[4].markdown(f"R$ {rec.valor:,.2f}")
            if rec.motivacao:
                with cols[5].expander("Ver motivacao", expanded=False):
                    st.markdown(rec.motivacao)
            else:
                cols[5].markdown("—")

            if cols[6].button("X", key=f"del_{rec.change_id}", help="Excluir registro"):
                st.session_state[f"confirm_del_{rec.change_id}"] = True

            if st.session_state.get(f"confirm_del_{rec.change_id}"):
                st.warning(f"Confirma exclusao do registro **{rec.ticker}** ({rec.acao}) de {rec.data_mudanca}?")
                cc1, cc2, _ = st.columns([1, 1, 4])
                if cc1.button("Sim, excluir", key=f"yes_del_{rec.change_id}", type="primary"):
                    delete_change(rec.change_id)
                    st.session_state.pop(f"confirm_del_{rec.change_id}", None)
                    st.rerun()
                if cc2.button("Cancelar", key=f"no_del_{rec.change_id}"):
                    st.session_state.pop(f"confirm_del_{rec.change_id}", None)
                    st.rerun()

            st.divider()
