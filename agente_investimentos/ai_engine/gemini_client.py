"""Cliente Gemini para geração de análises via IA."""

import re
import time
from typing import Optional

from google import genai
from google.genai import types

from agente_investimentos.config import GEMINI_API_KEY, GEMINI_MODEL, GEMINI_MAX_RETRIES, GEMINI_RATE_LIMIT_DELAY
from agente_investimentos.cache.cache_manager import CacheManager
from agente_investimentos.ai_engine.prompts import (
    build_stock_prompt,
    build_fii_prompt,
    build_generic_prompt,
    build_portfolio_prompt,
    build_deep_stock_prompt,
    build_deep_fii_prompt,
    build_deep_generic_prompt,
    build_sector_prompt,
    build_execution_prompt,
    build_news_impact_prompt,
    build_migration_prompt,
    build_daily_summary_prompt,
    build_period_summary_prompt,
)

_cache = CacheManager()
_last_call_time = 0.0
_client = None

# Safety settings permissivos para conteudo de notícias/política/economia
_SAFETY_SETTINGS = [
    types.SafetySetting(category="HARM_CATEGORY_HARASSMENT", threshold="BLOCK_ONLY_HIGH"),
    types.SafetySetting(category="HARM_CATEGORY_HATE_SPEECH", threshold="BLOCK_ONLY_HIGH"),
    types.SafetySetting(category="HARM_CATEGORY_SEXUALLY_EXPLICIT", threshold="BLOCK_ONLY_HIGH"),
    types.SafetySetting(category="HARM_CATEGORY_DANGEROUS_CONTENT", threshold="BLOCK_ONLY_HIGH"),
]

_GENERATION_CONFIG = types.GenerateContentConfig(
    safety_settings=_SAFETY_SETTINGS,
)


def _get_client():
    global _client
    if not GEMINI_API_KEY or GEMINI_API_KEY == "COLOQUE_SUA_CHAVE_GEMINI_AQUI":
        return None
    if _client is None:
        _client = genai.Client(api_key=GEMINI_API_KEY)
    return _client


def _rate_limit():
    global _last_call_time
    elapsed = time.time() - _last_call_time
    if elapsed < GEMINI_RATE_LIMIT_DELAY:
        time.sleep(GEMINI_RATE_LIMIT_DELAY - elapsed)
    _last_call_time = time.time()


def _extract_text_from_candidates(response) -> Optional[str]:
    """Extrai texto diretamente dos candidates (fallback quando response.text falha)."""
    try:
        if hasattr(response, 'candidates') and response.candidates:
            parts = response.candidates[0].content.parts
            text_parts = [p.text for p in parts if hasattr(p, 'text') and p.text]
            if text_parts:
                return "\n".join(text_parts)
    except Exception:
        pass
    return None


def _get_block_reason(response) -> str:
    """Retorna motivo do bloqueio se houver."""
    try:
        if hasattr(response, 'prompt_feedback') and response.prompt_feedback:
            return f"Prompt feedback: {response.prompt_feedback}"
        if hasattr(response, 'candidates') and response.candidates:
            c = response.candidates[0]
            if hasattr(c, 'finish_reason') and c.finish_reason:
                return f"Finish reason: {c.finish_reason}"
    except Exception:
        pass
    return ""


def _generate(prompt: str, config=None) -> Optional[str]:
    """Faz chamada ao Gemini com retries e safety settings permissivos."""
    client = _get_client()
    if client is None:
        print("[Gemini] API key não configurada ou inválida")
        return None

    gen_config = config or _GENERATION_CONFIG

    for attempt in range(2):  # máx 2 tentativas para não travar
        try:
            _rate_limit()
            response = client.models.generate_content(
                model=GEMINI_MODEL,
                contents=prompt,
                config=gen_config,
            )

            # Tenta response.text (pode levantar ValueError se bloqueado)
            text = None
            try:
                text = response.text
            except (ValueError, AttributeError) as text_err:
                print(f"[Gemini] response.text falhou: {text_err}")
                # Fallback: extrai direto dos candidates
                text = _extract_text_from_candidates(response)

            if text and text.strip():
                return text.strip()
            else:
                reason = _get_block_reason(response)
                print(f"[Gemini] Resposta vazia (tentativa {attempt+1}/2). {reason}")

        except Exception as e:
            err_str = str(e)
            if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
                print(f"[Gemini] Rate limited 429 (tentativa {attempt+1}/2)")
                if attempt == 0:
                    time.sleep(10)
            else:
                print(f"[Gemini] Erro (tentativa {attempt+1}/2): {err_str[:300]}")
                if attempt == 0:
                    time.sleep(3)

    print("[Gemini] Falhou após 2 tentativas")
    return None


def analyze_asset_ai(analysis: dict) -> str:
    ticker = analysis.get("ticker", "unknown")
    tipo = analysis.get("tipo", "")

    cache_key = f"ai_{ticker}"
    cached = _cache.get("fundamentals", cache_key)
    if cached is not None:
        return cached

    if tipo == "Acao":
        prompt = build_stock_prompt(analysis)
    elif tipo == "FII":
        prompt = build_fii_prompt(analysis)
    else:
        prompt = build_generic_prompt(analysis)

    result = _generate(prompt)
    if result:
        _cache.set("fundamentals", cache_key, result)
        return result
    return "Análise IA indisponível para este ativo."


def analyze_portfolio_ai(portfolio_analysis: dict, macro: dict) -> str:
    cache_key = "ai_portfolio_consolidated"
    cached = _cache.get("fundamentals", cache_key)
    if cached is not None:
        return cached

    prompt = build_portfolio_prompt(portfolio_analysis, macro)
    result = _generate(prompt)
    if result:
        _cache.set("fundamentals", cache_key, result)
        return result
    return "Análise consolidada IA indisponível."


def analyze_asset_deep_ai(analysis: dict, portfolio_analysis: dict = None) -> str:
    ticker = analysis.get("ticker", "unknown")
    tipo = analysis.get("tipo", "")

    cache_key = f"ai_deep_{ticker}"
    cached = _cache.get("fundamentals", cache_key)
    if cached is not None:
        return cached

    if tipo == "Acao":
        prompt = build_deep_stock_prompt(analysis, portfolio_analysis)
    elif tipo == "FII":
        prompt = build_deep_fii_prompt(analysis, portfolio_analysis)
    else:
        prompt = build_deep_generic_prompt(analysis, portfolio_analysis)

    result = _generate(prompt)
    if result:
        _cache.set("fundamentals", cache_key, result)
        return result
    return "Análise IA detalhada indisponível para este ativo."


def analyze_sector_ai(sector_name: str, sector_assets: list, macro: dict) -> str:
    """Gera análise IA para um setor da carteira.

    Args:
        sector_name: Nome do setor
        sector_assets: Lista de dicts com dados dos ativos do setor
        macro: Dados macroeconômicos

    Returns:
        Texto da análise setorial
    """
    # Normalizar nome do setor para cache key
    safe_name = re.sub(r"[^a-zA-Z0-9]", "_", sector_name.lower()).strip("_")
    cache_key = f"ai_sector_{safe_name}"

    cached = _cache.get("fundamentals", cache_key)
    if cached is not None:
        return cached

    prompt = build_sector_prompt(sector_name, sector_assets, macro)
    result = _generate(prompt)
    if result:
        _cache.set("fundamentals", cache_key, result)
        return result
    return ""


def analyze_execution_ai(portfolio_analysis: dict, asset_analyses: list, macro: dict) -> str:
    """Gera texto AI para o relatório de execução (visão holística da carteira).

    Args:
        portfolio_analysis: Análise consolidada da carteira
        asset_analyses: Lista de análises individuais por ativo
        macro: Dados macroeconômicos

    Returns:
        Texto com diagnóstico, recomendações e tabela de ações
    """
    cache_key = "ai_execution_report"
    cached = _cache.get("fundamentals", cache_key)
    if cached is not None:
        return cached

    prompt = build_execution_prompt(portfolio_analysis, asset_analyses, macro)
    result = _generate(prompt)
    if result:
        _cache.set("fundamentals", cache_key, result)
        return result
    return "Relatório de execução IA indisponível."


def analyze_news_impact_ai(
    news_articles: list,
    portfolio_analysis: dict,
    asset_analyses: list,
    macro: dict,
) -> str:
    """Gera análise de impacto das notícias na carteira via Gemini.

    Args:
        news_articles: Lista de notícias (título, categoria, fonte, data)
        portfolio_analysis: Análise consolidada da carteira
        asset_analyses: Lista de análises individuais por ativo
        macro: Dados macroeconômicos

    Returns:
        Texto com análise de impacto (8 seções)
    """
    if not news_articles:
        return "[ERRO] Nenhuma noticia disponível para analisar."
    prompt = build_news_impact_prompt(news_articles, portfolio_analysis, asset_analyses, macro)
    print(f"[Gemini] News impact: {len(news_articles)} notícias, prompt ~{len(prompt)} chars")
    # Usa config com mais tokens para análise profunda (8 seções)
    config = types.GenerateContentConfig(
        safety_settings=_SAFETY_SETTINGS,
        max_output_tokens=16384,
    )
    result = _generate(prompt, config=config)
    if result:
        return result
    return "[ERRO] Análise de impacto das notícias indisponível. Verifique o console para detalhes."


def analyze_migration_ai(
    portfolio_analysis: dict,
    asset_analyses: list,
    macro: dict,
    news_impact_text: str = "",
) -> str:
    """Gera recomendações de migração/rebalanceamento via Gemini.

    Args:
        portfolio_analysis: Análise consolidada
        asset_analyses: Lista de análises individuais
        macro: Dados macro
        news_impact_text: (Opcional) Texto da análise de impacto

    Returns:
        Texto com recomendações de migração (4 seções)
    """
    prompt = build_migration_prompt(portfolio_analysis, asset_analyses, macro, news_impact_text)
    print(f"[Gemini] Migration: {len(asset_analyses)} ativos, prompt ~{len(prompt)} chars")
    result = _generate(prompt)
    if result:
        return result
    return "[ERRO] Recomendações de migração indisponíveis. Verifique o console para detalhes."


def analyze_period_summary_ai(news_articles: list, period: str = "diario") -> str:
    """Gera resumo por periodo das noticias focado em Geopolitica, AI e Economia.

    Args:
        news_articles: Lista de noticias (titulo, categoria, fonte, data)
        period: "diario" | "semanal" | "mensal"

    Returns:
        Texto com resumo em 3 secoes
    """
    if not news_articles:
        return "[ERRO] Nenhuma noticia disponivel para resumo."
    prompt = build_period_summary_prompt(news_articles, period)
    print(f"[Gemini] {period.capitalize()} summary: {len(news_articles)} noticias, prompt ~{len(prompt)} chars")
    result = _generate(prompt)
    if result:
        return result
    return f"[ERRO] Resumo {period} indisponivel. Verifique o console para detalhes."


def analyze_daily_summary_ai(news_articles: list) -> str:
    """Gera resumo diario (wrapper retrocompativel para analyze_period_summary_ai)."""
    return analyze_period_summary_ai(news_articles, "diario")
