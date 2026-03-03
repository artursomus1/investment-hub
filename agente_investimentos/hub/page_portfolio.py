"""Página de Upload e Análise de Carteira do HUB."""

import streamlit as st
from pathlib import Path

from agente_investimentos.config import PASTA_PDFS
from agente_investimentos.dashboard.run_history import save_run
from agente_investimentos.dashboard.session_persistence import save_last_result
from agente_investimentos.hub.components import render_hero_header, render_footer


PHASE_TITLES = {
    1: "Leitura do PDF",
    2: "Classificação dos Ativos",
    3: "Coleta de Dados Externos",
    4: "Análise Individual dos Ativos",
    5: "Análise Consolidada da Carteira",
    6: "Análise IA (Gemini)",
    7: "Relatório Detalhado por Setor",
    8: "Relatório de Execução",
}


def _list_pdfs() -> list:
    """Lista PDFs disponíveis na pasta de coleta."""
    if not PASTA_PDFS.exists():
        return []
    return sorted(PASTA_PDFS.glob("*.pdf"), key=lambda p: p.stat().st_mtime, reverse=True)


def render():
    """Renderiza a página de análise de carteira."""
    render_hero_header("Análise de Carteira", "Faça upload ou selecione um PDF para iniciar a análise automatizada")

    # Tabs: Upload ou Selecionar existente
    tab_upload, tab_select = st.tabs(["Upload de PDF", "PDFs Existentes"])

    selected_pdf = None

    with tab_upload:
        uploaded = st.file_uploader(
            "Arraste o PDF da carteira XP Performance aqui",
            type=["pdf"],
            help="Formato aceito: PDF do relatório XP Performance",
        )
        if uploaded:
            PASTA_PDFS.mkdir(parents=True, exist_ok=True)
            dest = PASTA_PDFS / uploaded.name
            dest.write_bytes(uploaded.getvalue())
            st.success(f"PDF salvo em: {dest.name}")
            selected_pdf = dest

    with tab_select:
        pdfs = _list_pdfs()
        if not pdfs:
            st.info(f"Nenhum PDF encontrado em: {PASTA_PDFS}")
        else:
            selected_pdf_from_list = st.selectbox(
                "Selecione o PDF",
                options=pdfs,
                format_func=lambda p: p.name,
            )
            if selected_pdf_from_list:
                selected_pdf = selected_pdf_from_list

    if not selected_pdf:
        st.info("Selecione ou faça upload de um PDF para continuar.")
        return

    st.divider()
    st.markdown(f"**PDF selecionado:** `{selected_pdf.name}`")

    # Seletor de relatórios
    REPORT_OPTIONS = {
        "Detalhado (por setor)": "detalhado",
        "Execução (plano de acao)": "execução",
    }
    selected_labels = st.multiselect(
        "Relatórios a gerar",
        options=list(REPORT_OPTIONS.keys()),
        default=list(REPORT_OPTIONS.keys()),
        help="Escolha quais PDFs serão gerados. Desmarcar relatórios acelera a execução.",
    )
    selected_reports = [REPORT_OPTIONS[label] for label in selected_labels]

    if not selected_reports:
        st.warning("Selecione pelo menos um tipo de relatório.")
        return

    btn_col, _ = st.columns([1, 3])
    with btn_col:
        run_btn = st.button("EXECUTAR ANÁLISE", type="primary", use_container_width=True)

    if run_btn:
        _execute_analysis(selected_pdf, selected_reports)

    render_footer()


def _execute_analysis(pdf_path: Path, reports: list):
    """Executa o pipeline de análise com progresso em tempo real."""
    st.divider()

    progress_bar = st.progress(0.0)
    status_text = st.empty()
    phase_container = st.container()

    active_phases = [1, 2, 3, 4, 5]
    if "detalhado" in reports:
        active_phases += [6, 7]
    if "execução" in reports:
        active_phases.append(8)

    completed_phases = []
    current_phase_num = 0

    def on_progress(progress):
        nonlocal current_phase_num

        progress_bar.progress(min(progress.percent, 1.0))
        status_text.markdown(
            f"**Fase {progress.phase}/{len(active_phases)}** - {progress.phase_title}  \n"
            f"_{progress.detail}_ ({progress.percent*100:.0f}%)"
        )

        if progress.phase > current_phase_num:
            if current_phase_num > 0:
                completed_phases.append(current_phase_num)
            current_phase_num = progress.phase

        with phase_container:
            phase_container.empty()
            lines = []
            for p in range(1, 9):
                title = PHASE_TITLES.get(p, f"Fase {p}")
                if p not in active_phases:
                    lines.append(f"- [x] ~~Fase {p}: {title}~~ _(pulada)_")
                elif p in completed_phases:
                    lines.append(f"- [x] Fase {p}: {title}")
                elif p == progress.phase:
                    lines.append(f"- [ ] **Fase {p}: {title}** _(em andamento...)_")
                else:
                    lines.append(f"- [ ] Fase {p}: {title}")
            phase_container.markdown("\n".join(lines))

    try:
        from agente_investimentos.main import run
        result = run(pdf_path=pdf_path, progress_cb=on_progress, reports=reports)

        completed_phases.append(active_phases[-1])
        progress_bar.progress(1.0)
        status_text.markdown(f"**Concluído em {result['elapsed']:.1f}s**")

        with phase_container:
            phase_container.empty()
            lines = []
            for p in range(1, 9):
                title = PHASE_TITLES.get(p, f"Fase {p}")
                if p not in active_phases:
                    lines.append(f"- [x] ~~Fase {p}: {title}~~ _(pulada)_")
                else:
                    lines.append(f"- [x] Fase {p}: {title}")
            phase_container.markdown("\n".join(lines))

        record = save_run(result)

        st.divider()
        st.success(f"Análise concluída com sucesso em {result['elapsed']:.1f}s!")

        detailed_path = result.get("detailed_path")
        execution_path = result.get("execution_path")
        dl_cols = st.columns(2)

        with dl_cols[0]:
            if detailed_path and Path(str(detailed_path)).exists():
                dp = Path(str(detailed_path))
                st.download_button(
                    "Download PDF Detalhado",
                    data=dp.read_bytes(),
                    file_name=dp.name,
                    mime="application/pdf",
                    use_container_width=True,
                )

        with dl_cols[1]:
            if execution_path and Path(str(execution_path)).exists():
                ep = Path(str(execution_path))
                st.download_button(
                    "Download PDF Execução",
                    data=ep.read_bytes(),
                    file_name=ep.name,
                    mime="application/pdf",
                    use_container_width=True,
                )

        st.session_state["last_result"] = result
        st.session_state["last_record"] = record

        # Persiste em disco para sobreviver a refresh/reinicio
        save_last_result(result)

        st.info("Acesse **Dashboard** ou **Impacto das Notícias** no menu lateral.")

    except Exception as e:
        st.error(f"Erro na execução: {e}")
        import traceback
        st.code(traceback.format_exc())
