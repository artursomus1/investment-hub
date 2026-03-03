"""Página de Histórico de Execuções do HUB."""

import streamlit as st

from agente_investimentos.dashboard.run_history import load_all_runs
from agente_investimentos.hub.components import format_brl, render_hero_header, render_empty_state, render_footer


def render():
    """Renderiza a página de histórico."""
    render_hero_header("Histórico de Execuções", "Todas as análises realizadas")

    records = load_all_runs()

    if not records:
        render_empty_state("Nenhuma execução registrada ainda. Execute uma análise primeiro.")
        render_footer()
        st.stop()

    for i, rec in enumerate(records):
        ts_display = rec.timestamp[:16].replace("T", " ")
        with st.container():
            cols = st.columns([2, 2, 2, 1.5, 1.5, 1])
            cols[0].write(f"**{ts_display}**")
            cols[1].write(f"Cliente: {rec.client_code}")
            cols[2].write(format_brl(rec.total_bruto))
            cols[3].write(f"{rec.num_ativos} ativos")
            cols[4].write(f"{rec.elapsed:.0f}s")
            if cols[5].button("Ver", key=f"view_{rec.run_id}"):
                st.session_state["view_record_id"] = rec.run_id
                st.session_state.pop("last_result", None)
                st.rerun()
            st.divider()

    render_footer()
