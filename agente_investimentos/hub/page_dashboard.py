"""Página Dashboard do HUB - KPIs, gráficos, alertas."""

import streamlit as st
from pathlib import Path

from agente_investimentos.config import COR_VERDE_ESCURO, COR_AZUL
from agente_investimentos.dashboard.run_history import load_run
from agente_investimentos.dashboard.session_persistence import ensure_session_state
from agente_investimentos.hub.components import format_brl, render_hero_header, render_empty_state, render_footer


def render():
    """Renderiza a página de dashboard."""
    ensure_session_state()
    render_hero_header("Dashboard da Carteira", "Visão consolidada dos seus investimentos")

    result = st.session_state.get("last_result")
    selected_record_id = st.session_state.get("view_record_id")

    if selected_record_id:
        record = load_run(selected_record_id)
        if record:
            st.caption(f"Visualizando execução: {record.run_id} ({record.timestamp[:16]})")
            if not result or result.get("_record_id") != selected_record_id:
                _render_record_view(record)
                return

    if not result:
        render_empty_state("Nenhuma análise carregada. Execute uma análise em Análise de Carteira ou selecione no Histórico.")
        render_footer()
        st.stop()

    _render_full_dashboard(result)


def _render_record_view(record):
    """Renderiza dashboard simplificado a partir de um record do histórico."""
    st.divider()
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Patrimônio", format_brl(record.total_bruto))
    c2.metric("Ativos", record.num_ativos)
    c3.metric("Rent. Mês", f"{record.rent_mes_ponderada:.2f}%")
    c4.metric("Rent. Ano", f"{record.rent_ano_ponderada:.2f}%")
    c5.metric("Concentração", record.nivel_concentração)

    st.divider()
    col1, col2 = st.columns(2)

    with col1:
        if record.detailed_pdf:
            dp = Path(record.detailed_pdf)
            if dp.exists():
                st.download_button("Download PDF Detalhado", data=dp.read_bytes(),
                                   file_name=dp.name, mime="application/pdf", use_container_width=True)
            else:
                st.warning("PDF detalhado não encontrado no disco.")
        else:
            st.info("Relatório detalhado não foi gerado nesta execução.")

    with col2:
        if record.execution_pdf:
            ep = Path(record.execution_pdf)
            if ep.exists():
                st.download_button("Download PDF Execução", data=ep.read_bytes(),
                                   file_name=ep.name, mime="application/pdf", use_container_width=True)
            else:
                st.warning("PDF de execução não encontrado no disco.")
        else:
            st.info("Relatório de execução não foi gerado nesta execução.")

    st.info("Para ver gráficos e análises completas, execute a análise novamente.")
    render_footer()
    st.stop()


def _render_full_dashboard(result: dict):
    """Renderiza dashboard completo com gráficos."""
    portfolio = result["portfolio"]
    pa = result["portfolio_analysis"]
    macro = result.get("macro", {}) or {}
    asset_analyses = result["asset_analyses"]

    st.markdown(
        f'<p class="sub-header">Cliente: {portfolio.client_code} | '
        f'{portfolio.num_assets} ativos | Ref: {portfolio.data_referencia}</p>',
        unsafe_allow_html=True,
    )

    # KPIs
    st.divider()
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Patrimônio", format_brl(portfolio.total_bruto))
    c2.metric("Ativos", portfolio.num_assets)
    c3.metric("Rent. Mês", f"{pa['rent_mes_ponderada']:.2f}%")
    c4.metric("Rent. Ano", f"{pa['rent_ano_ponderada']:.2f}%")
    c5.metric("Concentração", pa["nivel_concentração"],
              delta=f"HHI: {pa['concentração_hhi']:.0f}", delta_color="off")

    # Alertas de risco
    risk_alerts = []
    for aa in asset_analyses:
        ticker = aa.get("ticker", "")
        alocacao = aa.get("alocacao", 0)
        rent_mes = aa.get("rent_mes", 0)
        if alocacao > 15:
            risk_alerts.append(f"**{ticker}**: alocacao elevada ({alocacao:.1f}%)")
        if rent_mes < -10:
            risk_alerts.append(f"**{ticker}**: queda forte no mês ({rent_mes:.1f}%)")

    if risk_alerts:
        st.divider()
        st.subheader("Alertas de Risco")
        for alert in risk_alerts[:10]:
            st.warning(alert)

    # Graficos
    st.divider()
    try:
        import plotly.express as px
        HAS_PLOTLY = True
    except ImportError:
        HAS_PLOTLY = False

    col_pie, col_bar = st.columns(2)

    with col_pie:
        st.subheader("Distribuição Setorial")
        dist_setor = pa.get("distribuição_setor", {})
        if dist_setor and HAS_PLOTLY:
            labels = list(dist_setor.keys())
            values = [d["alocacao"] for d in dist_setor.values()]
            fig = px.pie(names=labels, values=values,
                         color_discrete_sequence=px.colors.qualitative.Set3, hole=0.35)
            fig.update_layout(margin=dict(t=20, b=20, l=20, r=20), height=350,
                              legend=dict(font=dict(size=10)))
            st.plotly_chart(fig, use_container_width=True)
        elif dist_setor:
            for setor, dados in dist_setor.items():
                st.write(f"- {setor}: {dados['alocacao']:.1f}%")

    with col_bar:
        st.subheader("Distribuição por Tipo")
        dist_tipo = pa.get("distribuição_tipo", {})
        if dist_tipo and HAS_PLOTLY:
            tipos = list(dist_tipo.keys())
            saldos = [d["saldo"] for d in dist_tipo.values()]
            fig = px.bar(x=tipos, y=saldos, labels={"x": "Tipo", "y": "Saldo (R$)"},
                         color=tipos,
                         color_discrete_sequence=[COR_VERDE_ESCURO, COR_AZUL, "#28a745", "#ffc107", "#dc3545"])
            fig.update_layout(margin=dict(t=20, b=20, l=20, r=20), height=350, showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
        elif dist_tipo:
            for tipo, dados in dist_tipo.items():
                st.write(f"- {tipo}: R$ {dados['saldo']:,.2f}")

    # Top/Piores
    st.divider()
    col_top, col_worst = st.columns(2)

    with col_top:
        st.subheader("Top Performers (Mês)")
        top = pa.get("top_performers_mes", [])
        if top:
            for i, t in enumerate(top, 1):
                rv = t["rent"]
                color = "green" if rv >= 0 else "red"
                st.markdown(f"{i}. **{t['ticker']}** - <span style='color:{color}'>{rv:+.2f}%</span>",
                            unsafe_allow_html=True)

    with col_worst:
        st.subheader("Piores Performers (Mês)")
        worst = pa.get("piores_mes", [])
        if worst:
            for i, t in enumerate(worst, 1):
                rv = t["rent"]
                color = "green" if rv >= 0 else "red"
                st.markdown(f"{i}. **{t['ticker']}** - <span style='color:{color}'>{rv:+.2f}%</span>",
                            unsafe_allow_html=True)

    # Dados macro
    if macro:
        st.divider()
        st.subheader("Dados Macroeconômicos")
        mc1, mc2, mc3, mc4 = st.columns(4)
        mc1.metric("CDI Anual", f"{macro.get('cdi_anual', 'N/D')}%")
        mc2.metric("SELIC Meta", f"{macro.get('selic_meta', 'N/D')}%")
        mc3.metric("IPCA 12m", f"{macro.get('ipca_12m', 'N/D')}%")
        mc4.metric("CDI Mensal", f"{macro.get('cdi_mensal', 'N/D')}%")

    # Downloads
    st.divider()
    st.subheader("Downloads")
    col1, col2 = st.columns(2)
    detailed_path = result.get("detailed_path")
    execution_path = result.get("execution_path")

    with col1:
        if detailed_path and Path(str(detailed_path)).exists():
            dp = Path(str(detailed_path))
            st.download_button("Download PDF Detalhado", data=dp.read_bytes(),
                               file_name=dp.name, mime="application/pdf", use_container_width=True)

    with col2:
        if execution_path and Path(str(execution_path)).exists():
            ep = Path(str(execution_path))
            st.download_button("Download PDF Execução", data=ep.read_bytes(),
                               file_name=ep.name, mime="application/pdf", use_container_width=True)

    render_footer()
