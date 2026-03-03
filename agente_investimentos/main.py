"""Orquestrador principal do Agente de Investimentos - Pipeline de 8 fases."""

import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict, List, Any, Optional

from agente_investimentos.config import PASTA_SAIDA
from agente_investimentos.pdf_reader.extractor import find_pdf, extract_portfolio
from agente_investimentos.pdf_reader.models import PortfolioData
from agente_investimentos.analysis.asset_classifier import classify_all
from agente_investimentos.analysis.stock_analyzer import analyze_stock
from agente_investimentos.analysis.fii_analyzer import analyze_fii
from agente_investimentos.analysis.fixed_income_analyzer import analyze_fixed_income
from agente_investimentos.analysis.fund_analyzer import analyze_fund
from agente_investimentos.analysis.portfolio_analyzer import analyze_portfolio
from agente_investimentos.data_sources.bcb_client import get_macro_data
from agente_investimentos.data_sources.source_registry import SourceRegistry
from agente_investimentos.ai_engine.gemini_client import (
    analyze_asset_ai, analyze_asset_deep_ai, analyze_sector_ai,
    analyze_execution_ai,
)
from agente_investimentos.report.detailed_pdf_builder import DetailedReportBuilder
from agente_investimentos.report.execution_pdf_builder import ExecutionReportBuilder


@dataclass
class PhaseProgress:
    """Progresso de uma fase do pipeline."""
    phase: int
    total_phases: int
    phase_title: str
    detail: str
    percent: float  # 0.0 a 1.0


def _print_phase(num: int, title: str):
    print(f"\n{'='*60}")
    print(f"  FASE {num}: {title}")
    print(f"{'='*60}")


def _emit(cb: Optional[Callable], phase: int, title: str, detail: str, percent: float):
    """Emite progresso via callback (se fornecido)."""
    if cb:
        cb(PhaseProgress(
            phase=phase,
            total_phases=8,
            phase_title=title,
            detail=detail,
            percent=percent,
        ))


def run(
    pdf_path: Optional[Path] = None,
    progress_cb: Optional[Callable[[PhaseProgress], None]] = None,
    reports: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Executa o pipeline completo de análise.

    Args:
        pdf_path: Caminho do PDF. Se None, busca automaticamente na pasta de coleta.
        progress_cb: Callback opcional para reportar progresso (usado pelo dashboard).
        reports: Lista de relatórios a gerar. Opções: "detalhado", "execução".
                 Se None, gera ambos (backward compatible).

    Returns:
        Dict com todos os dados da execução:
        - portfolio: PortfolioData
        - asset_analyses: lista de análises por ativo
        - portfolio_analysis: análise consolidada
        - macro: dados macroeconômicos
        - ai_texts: textos IA por ativo (vazio se detalhado não solicitado)
        - deep_ai_texts: textos IA detalhados por ativo (vazio se detalhado não solicitado)
        - sector_ai_texts: textos IA por setor (vazio se detalhado não solicitado)
        - detailed_path: Path do PDF detalhado (None se não solicitado)
        - execution_path: Path do PDF de execução (None se não solicitado)
        - sources_path: Path do JSON de fontes
        - elapsed: tempo total em segundos
        - reports_generated: lista de relatórios gerados
    """
    if reports is None:
        reports = ["detalhado", "execução"]
    gen_detailed = "detalhado" in reports
    gen_execution = "execução" in reports
    start = time.time()
    registry = SourceRegistry()

    # ===== FASE 1: Leitura do PDF =====
    _print_phase(1, "LEITURA DO PDF")
    _emit(cb=progress_cb, phase=1, title="Leitura do PDF",
          detail="Extraindo dados do PDF...", percent=0.0)

    if pdf_path is None:
        pdf_path = find_pdf()

    print(f"  Arquivo: {pdf_path.name}")
    portfolio = extract_portfolio(pdf_path)
    print(f"  Cliente: {portfolio.client_code}")
    print(f"  Ativos encontrados: {portfolio.num_assets}")
    print(f"  Patrimônio bruto: R$ {portfolio.total_bruto:,.2f}")
    registry.add("PDF", "XP Performance", str(pdf_path), portfolio.client_code, "ok")
    _emit(cb=progress_cb, phase=1, title="Leitura do PDF",
          detail=f"PDF lido: {portfolio.num_assets} ativos", percent=0.04)

    # ===== FASE 2: Classificação dos Ativos =====
    _print_phase(2, "CLASSIFICAÇÃO DOS ATIVOS")
    _emit(cb=progress_cb, phase=2, title="Classificação dos Ativos",
          detail="Classificando ativos...", percent=0.04)

    classify_all(portfolio.assets)

    tipos = {}
    for a in portfolio.assets:
        tipos[a.tipo] = tipos.get(a.tipo, 0) + 1
    for tipo, count in sorted(tipos.items()):
        print(f"  {tipo}: {count} ativo(s)")
    _emit(cb=progress_cb, phase=2, title="Classificação dos Ativos",
          detail=f"Classificados: {', '.join(f'{t}:{c}' for t,c in sorted(tipos.items()))}",
          percent=0.08)

    # ===== FASE 3: Coleta de Dados Externos =====
    _print_phase(3, "COLETA DE DADOS EXTERNOS")
    _emit(cb=progress_cb, phase=3, title="Coleta de Dados Externos",
          detail="Buscando dados BCB...", percent=0.08)

    print("  Buscando dados macroeconômicos (BCB)...")
    macro = get_macro_data(registry)
    if macro:
        cdi = macro.get("cdi_anual", "N/D")
        selic = macro.get("selic_meta", "N/D")
        print(f"  CDI anual: {cdi}% | SELIC meta: {selic}%")
    _emit(cb=progress_cb, phase=3, title="Coleta de Dados Externos",
          detail="Dados macro coletados", percent=0.12)

    # ===== FASE 4: Análise Individual dos Ativos =====
    _print_phase(4, "ANÁLISE INDIVIDUAL DOS ATIVOS")
    _emit(cb=progress_cb, phase=4, title="Análise Individual dos Ativos",
          detail="Iniciando análise por ativo...", percent=0.12)

    asset_analyses: List[Dict[str, Any]] = []
    analyzers = {
        "Acao": analyze_stock,
        "FII": analyze_fii,
        "RF": analyze_fixed_income,
        "Fundo": analyze_fund,
    }

    n_assets = portfolio.num_assets
    for i, asset in enumerate(portfolio.assets, 1):
        analyzer = analyzers.get(asset.tipo, analyze_fund)
        print(f"  [{i}/{n_assets}] {asset.ticker} ({asset.tipo})...", end=" ")
        # Progresso: 12% a 37% (25% divididos por N ativos)
        pct = 0.12 + (i / n_assets) * 0.25
        _emit(cb=progress_cb, phase=4, title="Análise Individual dos Ativos",
              detail=f"[{i}/{n_assets}] {asset.ticker} ({asset.tipo})",
              percent=pct)
        try:
            result = analyzer(asset, registry)
            asset_analyses.append(result)
            print("OK")
        except Exception as e:
            print(f"ERRO: {e}")
            asset_analyses.append({
                "ticker": asset.ticker,
                "nome": asset.nome,
                "tipo": asset.tipo,
                "saldo_bruto": asset.saldo_bruto,
                "alocacao": asset.alocacao,
                "rent_mes": asset.rent_mes,
                "rent_ano": asset.rent_ano,
                "cdi_mes": asset.cdi_mes,
                "cdi_ano": asset.cdi_ano,
                "fundamentals": {},
                "dividends": [],
                "news": [],
                "historical_prices": [],
            })

    # ===== FASE 5: Análise Consolidada =====
    _print_phase(5, "ANÁLISE CONSOLIDADA DA CARTEIRA")
    _emit(cb=progress_cb, phase=5, title="Análise Consolidada da Carteira",
          detail="Calculando métricas consolidadas...", percent=0.37)

    portfolio_analysis = analyze_portfolio(portfolio, asset_analyses)
    print(f"  Rent. ponderada mes: {portfolio_analysis['rent_mes_ponderada']:.2f}%")
    print(f"  Rent. ponderada ano: {portfolio_analysis['rent_ano_ponderada']:.2f}%")
    print(f"  Concentração: {portfolio_analysis['nivel_concentração']} (HHI: {portfolio_analysis['concentração_hhi']:.0f})")

    dist_setor = portfolio_analysis.get("distribuição_setor", {})
    print(f"  Setores identificados: {len(dist_setor)}")
    for setor, dados in list(dist_setor.items())[:8]:
        print(f"    - {setor}: {dados['count']} ativo(s), {dados['alocacao']:.1f}%")
    if len(dist_setor) > 8:
        print(f"    ... e mais {len(dist_setor) - 8} setor(es)")
    _emit(cb=progress_cb, phase=5, title="Análise Consolidada da Carteira",
          detail=f"HHI: {portfolio_analysis['concentração_hhi']:.0f} ({portfolio_analysis['nivel_concentração']})",
          percent=0.40)

    # ===== FASE 6: Análise IA (Gemini) =====
    ai_texts: Dict[str, str] = {}
    deep_ai_texts: Dict[str, str] = {}
    sector_ai_texts: Dict[str, str] = {}
    detailed_path = None

    if gen_detailed:
        _print_phase(6, "ANÁLISE IA (GEMINI)")
        _emit(cb=progress_cb, phase=6, title="Análise IA (Gemini)",
              detail="Gerando análises IA por ativo...", percent=0.40)

        for i, analysis in enumerate(asset_analyses, 1):
            ticker = analysis.get("ticker", "")
            print(f"  [{i}/{len(asset_analyses)}] Gerando análise IA: {ticker}...", end=" ")
            pct = 0.40 + (i / len(asset_analyses)) * 0.20
            _emit(cb=progress_cb, phase=6, title="Análise IA (Gemini)",
                  detail=f"[{i}/{len(asset_analyses)}] IA: {ticker}",
                  percent=pct)
            try:
                ai_text = analyze_asset_ai(analysis)
                ai_texts[ticker] = ai_text
                if ai_text and "indisponível" not in ai_text.lower():
                    print("OK")
                else:
                    print("N/D")
            except Exception as e:
                print(f"ERRO: {e}")
                ai_texts[ticker] = ""

        # ===== FASE 7: Relatório Detalhado por Setor =====
        _print_phase(7, "RELATÓRIO DETALHADO POR SETOR")
        _emit(cb=progress_cb, phase=7, title="Relatório Detalhado por Setor",
              detail="Gerando análises IA aprofundadas...", percent=0.60)

        n_deep = len(asset_analyses)
        n_sectors = len(dist_setor)
        total_f7 = n_deep + n_sectors + 1

        for i, analysis in enumerate(asset_analyses, 1):
            ticker = analysis.get("ticker", "")
            print(f"  [{i}/{n_deep}] IA detalhada: {ticker}...", end=" ")
            pct = 0.60 + (i / total_f7) * 0.30
            _emit(cb=progress_cb, phase=7, title="Relatório Detalhado por Setor",
                  detail=f"[{i}/{n_deep}] IA detalhada: {ticker}",
                  percent=pct)
            try:
                deep_text = analyze_asset_deep_ai(analysis, portfolio_analysis)
                if deep_text and "indisponível" not in deep_text.lower():
                    deep_ai_texts[ticker] = deep_text
                    print("OK")
                else:
                    fallback = ai_texts.get(ticker, "")
                    if fallback and "indisponível" not in fallback.lower():
                        deep_ai_texts[ticker] = fallback
                        print("(fallback)")
                    else:
                        deep_ai_texts[ticker] = ""
                        print("N/D")
            except Exception as e:
                deep_ai_texts[ticker] = ai_texts.get(ticker, "")
                print("(fallback)")

        print(f"  Gerando análises setoriais ({n_sectors} setores)...")
        for i, (sector_name, sector_data) in enumerate(dist_setor.items(), 1):
            print(f"  [{i}/{n_sectors}] Setor: {sector_name}...", end=" ")
            step = n_deep + i
            pct = 0.60 + (step / total_f7) * 0.30
            _emit(cb=progress_cb, phase=7, title="Relatório Detalhado por Setor",
                  detail=f"[{i}/{n_sectors}] Setor: {sector_name}",
                  percent=pct)
            try:
                sector_text = analyze_sector_ai(sector_name, sector_data.get("ativos", []), macro)
                if sector_text:
                    sector_ai_texts[sector_name] = sector_text
                    print("OK")
                else:
                    sector_ai_texts[sector_name] = ""
                    print("N/D")
            except Exception as e:
                print(f"ERRO: {e}")
                sector_ai_texts[sector_name] = ""

        print("  Montando relatório detalhado por setor...")
        _emit(cb=progress_cb, phase=7, title="Relatório Detalhado por Setor",
              detail="Montando PDF detalhado...", percent=0.88)
        detailed_builder = DetailedReportBuilder(
            portfolio=portfolio,
            asset_analyses=asset_analyses,
            deep_ai_texts=deep_ai_texts,
            sources=registry.to_list(),
            sector_ai_texts=sector_ai_texts,
            portfolio_analysis=portfolio_analysis,
        )

        detailed_path = detailed_builder.build()
        print(f"  Relatório detalhado salvo em: {detailed_path}")
        _emit(cb=progress_cb, phase=7, title="Relatório Detalhado por Setor",
              detail=f"PDF detalhado: {detailed_path.name}", percent=0.90)
    else:
        print(f"\n  [Fases 6-7 puladas: relatório detalhado não solicitado]")
        _emit(cb=progress_cb, phase=6, title="Pulando Fases 6-7",
              detail="Relatório detalhado não solicitado", percent=0.90)

    # ===== FASE 8: Relatório de Execução =====
    execution_path = None

    if gen_execution:
        _print_phase(8, "RELATÓRIO DE EXECUÇÃO")
        _emit(cb=progress_cb, phase=8, title="Relatório de Execução",
              detail="Gerando análise IA de execução...", percent=0.90)

        print("  Gerando análise IA de execução...", end=" ")
        try:
            execution_ai = analyze_execution_ai(portfolio_analysis, asset_analyses, macro)
            if execution_ai and "indisponível" not in execution_ai.lower():
                print("OK")
            else:
                print("N/D")
        except Exception as e:
            print(f"ERRO: {e}")
            execution_ai = "Relatório de execução IA indisponível."

        print("  Montando relatório de execução...")
        _emit(cb=progress_cb, phase=8, title="Relatório de Execução",
              detail="Montando PDF de execução...", percent=0.95)
        execution_builder = ExecutionReportBuilder(
            portfolio=portfolio,
            portfolio_analysis=portfolio_analysis,
            asset_analyses=asset_analyses,
            execution_ai=execution_ai,
            macro=macro,
        )

        execution_path = execution_builder.build()
        print(f"  Relatório de execução salvo em: {execution_path}")
    else:
        print(f"\n  [Fase 8 pulada: relatório de execução não solicitado]")

    # Salvar registro de fontes
    sources_path = PASTA_SAIDA / f"{portfolio.client_code}_fontes.json"
    registry.save(sources_path)
    print(f"  Fontes salvas em: {sources_path}")

    elapsed = time.time() - start
    generated = []
    print(f"\n{'='*60}")
    print(f"  CONCLUÍDO em {elapsed:.1f}s")
    if detailed_path:
        print(f"  1. Detalhado: {detailed_path.name}")
        generated.append("detalhado")
    if execution_path:
        print(f"  2. Execução:  {execution_path.name}")
        generated.append("execução")
    print(f"  {registry.summary}")
    print(f"{'='*60}\n")

    _emit(cb=progress_cb, phase=8, title="Concluído",
          detail=f"Finalizado em {elapsed:.1f}s", percent=1.0)

    return {
        "portfolio": portfolio,
        "asset_analyses": asset_analyses,
        "portfolio_analysis": portfolio_analysis,
        "macro": macro,
        "ai_texts": ai_texts,
        "deep_ai_texts": deep_ai_texts,
        "sector_ai_texts": sector_ai_texts,
        "detailed_path": detailed_path,
        "execution_path": execution_path,
        "sources_path": sources_path,
        "elapsed": elapsed,
        "reports_generated": generated,
    }
