"""Templates de prompts em português para análise via Gemini."""


def build_stock_prompt(analysis: dict) -> str:
    """Prompt para análise individual de ação."""
    fund = analysis.get("fundamentals", {})
    divs = analysis.get("dividends", [])
    news = analysis.get("news", [])

    news_text = ""
    if news:
        news_text = "\n".join(f"- {n['título']}" for n in news[:3])
    else:
        news_text = "Nenhuma notícia recente encontrada."

    div_text = ""
    if divs:
        div_text = f"Últimos {len(divs)} dividendos registrados."
    else:
        div_text = "Sem dados de dividendos."

    return f"""Você é um analista de investimentos brasileiro experiente. Análise o ativo abaixo e forneça uma avaliação concisa e profissional em português.

ATIVO: {analysis['ticker']} - {analysis['nome']}
TIPO: Ação

DADOS DA CARTEIRA (PDF XP Performance):
- Saldo bruto: R$ {analysis['saldo_bruto']:,.2f}
- Alocação: {analysis['alocacao']:.2f}%
- Rentabilidade mês: {analysis['rent_mes']:.2f}%
- %CDI mês: {analysis['cdi_mes']:.2f}%
- Rentabilidade ano: {analysis['rent_ano']:.2f}%
- %CDI ano: {analysis['cdi_ano']:.2f}%

DADOS FUNDAMENTALISTAS:
- Preço atual: {fund.get('preço', 'N/D')}
- P/L: {fund.get('p_l', 'N/D')}
- P/VP: {fund.get('p_vp', 'N/D')}
- ROE: {fund.get('roe', 'N/D')}
- Dividend Yield: {fund.get('dividend_yield', 'N/D')}
- Margem EBIT: {fund.get('ebit_margin', 'N/D')}
- Margem Líquida: {fund.get('net_margin', 'N/D')}
- Dív. Líq./EBITDA: {fund.get('divida_líquida_ebitda', 'N/D')}
- Setor: {fund.get('setor', 'N/D')}
- Indústria: {fund.get('industria', 'N/D')}

DIVIDENDOS: {div_text}

NOTÍCIAS RECENTES:
{news_text}

Forneça sua análise em formato estruturado com:
1. RESUMO (2-3 frases sobre o ativo)
2. PONTOS POSITIVOS (até 3 bullets)
3. PONTOS DE ATENÇÃO (até 3 bullets)
4. PERSPECTIVA (1-2 frases sobre expectativa)

Seja objetivo, use dados concretos quando disponíveis. Não faça recomendações de compra/venda."""


def build_fii_prompt(analysis: dict) -> str:
    """Prompt para análise individual de FII."""
    fund = analysis.get("fundamentals", {})

    return f"""Você é um analista de fundos imobiliários brasileiro. Análise o FII abaixo de forma concisa e profissional em português.

ATIVO: {analysis['ticker']} - {analysis['nome']}
TIPO: Fundo Imobiliário (FII)

DADOS DA CARTEIRA (PDF XP Performance):
- Saldo bruto: R$ {analysis['saldo_bruto']:,.2f}
- Alocação: {analysis['alocacao']:.2f}%
- Rentabilidade mês: {analysis['rent_mes']:.2f}%
- Rentabilidade ano: {analysis['rent_ano']:.2f}%

DADOS DE MERCADO:
- Preço: {fund.get('preço', 'N/D')}
- P/VP: {fund.get('p_vp', 'N/D')}
- Dividend Yield: {fund.get('dividend_yield', 'N/D')}

Forneça análise em formato estruturado:
1. RESUMO (2-3 frases)
2. PONTOS POSITIVOS (até 3 bullets)
3. PONTOS DE ATENÇÃO (até 3 bullets)
4. PERSPECTIVA (1-2 frases)

Seja objetivo. Não faça recomendações de compra/venda."""


def build_generic_prompt(analysis: dict) -> str:
    """Prompt genérico para RF e Fundos."""
    return f"""Você é um analista de investimentos brasileiro. Análise o ativo abaixo de forma breve e profissional em português.

ATIVO: {analysis['nome']}
TIPO: {analysis['tipo']}

DADOS DA CARTEIRA (PDF XP Performance):
- Saldo bruto: R$ {analysis['saldo_bruto']:,.2f}
- Alocação: {analysis['alocacao']:.2f}%
- Rentabilidade mês: {analysis['rent_mes']:.2f}%
- %CDI mês: {analysis['cdi_mes']:.2f}%
- Rentabilidade ano: {analysis['rent_ano']:.2f}%
- %CDI ano: {analysis['cdi_ano']:.2f}%

Forneça uma análise breve (3-5 frases) sobre o desempenho deste ativo, considerando o %CDI como referência. Seja objetivo. Não faça recomendações de compra/venda."""


def build_portfolio_prompt(portfolio_analysis: dict, macro: dict) -> str:
    """Prompt para análise consolidada da carteira."""
    tipo_dist = portfolio_analysis.get("distribuição_tipo", {})
    tipo_text = "\n".join(
        f"  - {k}: {v['count']} ativos, R$ {v['saldo']:,.2f} ({v['alocacao']:.1f}%)"
        for k, v in tipo_dist.items()
    )

    top = portfolio_analysis.get("top_performers_mes", [])
    top_text = "\n".join(f"  - {t['ticker']}: {t['rent']:.2f}%" for t in top[:5])

    piores = portfolio_analysis.get("piores_mes", [])
    piores_text = "\n".join(f"  - {t['ticker']}: {t['rent']:.2f}%" for t in piores[:3])

    return f"""Você é um consultor de investimentos sênior brasileiro. Análise a carteira completa abaixo e forneça uma visão consolidada profissional em português.

CARTEIRA:
- Total bruto: R$ {portfolio_analysis['total_bruto']:,.2f}
- Número de ativos: {portfolio_analysis['num_ativos']}
- Rentabilidade ponderada mês: {portfolio_analysis['rent_mes_ponderada']:.2f}%
- Rentabilidade ponderada ano: {portfolio_analysis['rent_ano_ponderada']:.2f}%
- Concentração (HHI): {portfolio_analysis['concentração_hhi']:.0f} ({portfolio_analysis['nivel_concentração']})

DISTRIBUIÇÃO POR TIPO:
{tipo_text}

MELHORES DO MÊS:
{top_text}

PIORES DO MÊS:
{piores_text}

CENÁRIO MACRO:
- CDI anual: {macro.get('cdi_anual', 'N/D')}%
- SELIC meta: {macro.get('selic_meta', 'N/D')}%
- IPCA mensal: {macro.get('ipca_mensal', 'N/D')}%

Forneça análise consolidada em formato estruturado:
1. VISÃO GERAL (3-4 frases sobre a carteira)
2. PONTOS FORTES (até 4 bullets)
3. PONTOS DE ATENÇÃO (até 4 bullets)
4. SUGESTÕES DE OTIMIZAÇÃO (até 3 bullets genéricos - sem citar ativos específicos para compra)

Seja profissional e equilibrado. Não faça recomendações específicas de compra/venda."""


# ============================================================
# PROMPTS PROFUNDOS - Relatório Detalhado
# ============================================================

def _build_hist_context(analysis: dict) -> str:
    """Monta contexto histórico a partir dos dados de preço."""
    hist = analysis.get("historical_prices", [])
    if not hist or len(hist) < 2:
        return "DADOS HISTORICOS: Indisponíveis."

    closes = [h.get("close") for h in hist if h.get("close")]
    if len(closes) < 2:
        return "DADOS HISTORICOS: Indisponíveis."

    first, last = closes[0], closes[-1]
    mx, mn = max(closes), min(closes)
    var_pct = ((last / first) - 1) * 100 if first else 0

    volumes = [h.get("volume", 0) for h in hist if h.get("volume")]
    vol_medio = sum(volumes) / len(volumes) if volumes else 0

    returns = [(closes[i] / closes[i-1] - 1) for i in range(1, len(closes)) if closes[i-1]]
    import statistics
    volatility = statistics.stdev(returns) * (252 ** 0.5) * 100 if len(returns) > 1 else 0

    return f"""DADOS HISTORICOS (12 MESES):
- Preco inicial: R$ {first:.2f}
- Preco atual: R$ {last:.2f}
- Variacao período: {var_pct:+.1f}%
- Maxima: R$ {mx:.2f} | Minima: R$ {mn:.2f}
- Volume medio diario: {vol_medio:,.0f}
- Volatilidade anualizada: {volatility:.1f}%
- Pregoes: {len(hist)}"""


def _build_news_text(news: list, limit: int = 8) -> str:
    if not news:
        return "Nenhuma noticia recente."
    items = []
    for n in news[:limit]:
        fonte = n.get('fonte', '')
        data = n.get('data', '')[:16] if n.get('data') else ''
        meta = f" [{fonte}]" if fonte else ""
        if data:
            meta += f" ({data})"
        items.append(f"- {n['título']}{meta}")
    return "\n".join(items)


def _get_news_sources(news: list) -> str:
    """Extrai lista unica de fontes de notícias."""
    if not news:
        return ""
    fontes = []
    for n in news:
        fonte = n.get("fonte", "")
        if fonte and fonte not in fontes:
            fontes.append(fonte)
    return ", ".join(fontes) if fontes else ""


def _build_portfolio_context(analysis: dict, portfolio_analysis: dict = None) -> str:
    """Monta contexto de portfolio para prompts aprofundados."""
    if not portfolio_analysis:
        return ""

    total = portfolio_analysis.get("total_bruto", 0)
    alocacao = analysis.get("alocacao", 0)
    saldo = analysis.get("saldo_bruto", 0)

    # Determinar importância estratégica
    tipo = analysis.get("tipo", "")
    rent_ano = analysis.get("rent_ano", 0)
    cdi_ano = analysis.get("cdi_ano", 0)
    fund = analysis.get("fundamentals", {})
    dy = fund.get("dividend_yield")

    papel = "Diversificacao"
    if tipo in ("RF",):
        papel = "Protecao e renda previsivel"
    elif tipo == "Fundo":
        papel = "Diversificacao e gestao profissional"
    elif tipo == "FII":
        papel = "Geração de renda passiva (rendimentos mensais)"
    elif tipo == "Acao":
        if dy and dy > 5:
            papel = "Geração de renda (dividendos)"
        elif rent_ano > 15:
            papel = "Crescimento de capital"
        else:
            papel = "Exposição a renda variavel"

    lines = [
        f"\nCONTEXTO DO PORTFOLIO:",
        f"- Carteira total: R$ {total:,.2f}",
        f"- Este ativo representa {alocacao:.2f}% da carteira (R$ {saldo:,.2f})",
        f"- Papel estrategico: {papel}",
    ]
    return "\n".join(lines)


def _build_potential_context(fund: dict) -> str:
    """Monta contexto de potencial de alta/baixa."""
    lines = []
    dist_high = fund.get("distancia_52w_high")
    dist_low = fund.get("distancia_52w_low")
    high = fund.get("fiftyTwoWeekHigh")
    low = fund.get("fiftyTwoWeekLow")
    vol = fund.get("volatilidade")
    sens = fund.get("score_sensibilidade")

    if dist_high is not None or vol is not None:
        lines.append("\nPOTENCIAL E SENSIBILIDADE:")
        if high is not None:
            lines.append(f"- Maxima 52 semanas: R$ {high:.2f} (distancia: {dist_high:+.1f}%)")
        if low is not None:
            lines.append(f"- Minima 52 semanas: R$ {low:.2f} (acima da minima: {dist_low:+.1f}%)")
        if vol is not None:
            lines.append(f"- Volatilidade anualizada: {vol:.1f}%")
        if sens:
            lines.append(f"- Sensibilidade: {sens}")

    return "\n".join(lines) if lines else ""


def build_deep_stock_prompt(analysis: dict, portfolio_analysis: dict = None) -> str:
    """Prompt aprofundado para ação no relatório detalhado."""
    fund = analysis.get("fundamentals", {})
    divs = analysis.get("dividends", [])
    news = analysis.get("news", [])
    hist_ctx = _build_hist_context(analysis)
    news_text = _build_news_text(news)
    news_sources = _get_news_sources(news)
    portfolio_ctx = _build_portfolio_context(analysis, portfolio_analysis)
    potential_ctx = _build_potential_context(fund)

    div_text = "Sem dados de dividendos."
    if divs:
        total_div = sum(d.get("rate", 0) for d in divs)
        div_text = f"{len(divs)} proventos registrados. Total: R$ {total_div:.2f}"

    return f"""Você e um analista de investimentos brasileiro experiente e detalhista.
Análise o ativo abaixo de forma APROFUNDADA e profissional em portugues.

ATIVO: {analysis['ticker']} - {analysis['nome']}
TIPO: Acao

DADOS DA CARTEIRA (PDF XP Performance):
- Saldo bruto: R$ {analysis['saldo_bruto']:,.2f}
- Alocacao: {analysis['alocacao']:.2f}%
- Rentabilidade mes: {analysis['rent_mes']:.2f}%
- %CDI mes: {analysis['cdi_mes']:.2f}%
- Rentabilidade ano: {analysis['rent_ano']:.2f}%
- %CDI ano: {analysis['cdi_ano']:.2f}%
{portfolio_ctx}

DADOS FUNDAMENTALISTAS:
- Preco: {fund.get('preço', 'N/D')} | P/L: {fund.get('p_l', 'N/D')} | P/VP: {fund.get('p_vp', 'N/D')}
- ROE: {fund.get('roe', 'N/D')} | DY: {fund.get('dividend_yield', 'N/D')}
- Margem EBIT: {fund.get('ebit_margin', 'N/D')} | Margem Liq: {fund.get('net_margin', 'N/D')}
- Div.Liq./EBITDA: {fund.get('divida_líquida_ebitda', 'N/D')}
- LPA: {fund.get('lpa', 'N/D')} | VPA: {fund.get('vpa', 'N/D')}
- Market Cap: {fund.get('market_cap', 'N/D')}
- Setor: {fund.get('setor', 'N/D')} | Industria: {fund.get('industria', 'N/D')}
{potential_ctx}

{hist_ctx}

DIVIDENDOS: {div_text}

MANCHETES DE NOTICIAS RECENTES:
{news_text}

Forneça análise DETALHADA e estruturada:
1. RESUMO EXECUTIVO (3-5 frases, visão geral e momento)
2. CENARIO DA EMPRESA (descreva o que a empresa faz, seu momento atual, estrategia recente, posição no mercado)
3. ENDIVIDAMENTO E ALAVANCAGEM (análise a relação com dividas usando Div.Liq./EBITDA e outros indicadores. A empresa esta saudavel? Qual o nivel de alavancagem? Riscos de crédito?)
4. ANÁLISE FUNDAMENTALISTA (avaliar multiplos, margens, comparar com pares do setor)
5. COMPORTAMENTO HISTORICO (tendencia de preço, volatilidade, suportes/resistencias)
6. PROVENTOS (consistencia, yield, sustentabilidade)
7. POTENCIAL E SENSIBILIDADE (distancia do topo 52s, volatilidade, potencial de alta/baixa)
8. RESUMO DE NOTICIAS (faça um RESUMO das principais notícias recentes sobre a empresa, baseado nas manchetes acima e no seu conhecimento. Ao final escreva: "Ultimas notícias resumidas a partir de: {news_sources}")
9. PONTOS POSITIVOS (ate 5 bullets)
10. RISCOS E ATENCAO (ate 5 bullets)
11. PERSPECTIVA (3-4 frases, curto e medio prazo)

Use dados concretos. Comente sobre cenario da empresa e alavancagem. Não faça recomendações de compra/venda."""


def build_deep_fii_prompt(analysis: dict, portfolio_analysis: dict = None) -> str:
    """Prompt aprofundado para FII no relatório detalhado."""
    fund = analysis.get("fundamentals", {})
    divs = analysis.get("dividends", [])
    news = analysis.get("news", [])
    hist_ctx = _build_hist_context(analysis)
    news_text = _build_news_text(news)
    news_sources = _get_news_sources(news)
    portfolio_ctx = _build_portfolio_context(analysis, portfolio_analysis)
    potential_ctx = _build_potential_context(fund)

    div_text = "Sem dados de rendimentos."
    if divs:
        total_div = sum(d.get("rate", 0) for d in divs)
        div_text = f"{len(divs)} rendimentos. Total 12m: R$ {total_div:.2f}"

    return f"""Você e um analista de fundos imobiliarios brasileiro experiente.
Análise o FII abaixo de forma APROFUNDADA em portugues.

ATIVO: {analysis['ticker']} - {analysis['nome']}
TIPO: Fundo Imobiliario (FII)

DADOS DA CARTEIRA:
- Saldo bruto: R$ {analysis['saldo_bruto']:,.2f}
- Alocacao: {analysis['alocacao']:.2f}%
- Rentabilidade mes: {analysis['rent_mes']:.2f}% | Ano: {analysis['rent_ano']:.2f}%
- %CDI mes: {analysis['cdi_mes']:.2f}% | %CDI ano: {analysis['cdi_ano']:.2f}%
{portfolio_ctx}

DADOS DE MERCADO:
- Preco: {fund.get('preço', 'N/D')} | P/VP: {fund.get('p_vp', 'N/D')}
- DY: {fund.get('dividend_yield', 'N/D')} | Market Cap: {fund.get('market_cap', 'N/D')}
- Setor: {fund.get('setor', 'N/D')}
{potential_ctx}

{hist_ctx}

RENDIMENTOS: {div_text}

MANCHETES DE NOTICIAS RECENTES:
{news_text}

Forneça análise DETALHADA e estruturada:
1. RESUMO EXECUTIVO (3-5 frases, visão geral e momento)
2. CENARIO DO FUNDO (descreva o que o fundo faz, tipo de ativos que possui, estrategia de gestao, posição no mercado de FIIs. Se e de tijolo: tipos de imoveis, localizacao, qualidade dos ativos. Se e de papel: tipos de CRIs, indexadores, qualidade de crédito)
3. ENDIVIDAMENTO E ALAVANCAGEM (o fundo tem alavancagem? Qual o nivel de comprometimento? CRIs emitidos? Riscos de crédito dos locatarios/devedores? Vacancia fisica e financeira?)
4. ANÁLISE DE VALOR (P/VP, desconto/premio ao VP, comparar com media FIIs do segmento)
5. RENDIMENTOS (consistencia mensal, yield anualizado, sustentabilidade dos proventos)
6. POTENCIAL E SENSIBILIDADE (distancia do topo 52s, volatilidade, potencial de valorizacao)
7. COMPORTAMENTO HISTORICO (tendencia cota, volatilidade)
8. RESUMO DE NOTICIAS (faça um RESUMO das principais notícias recentes sobre o fundo, baseado nas manchetes acima e no seu conhecimento. Ao final escreva: "Ultimas notícias resumidas a partir de: {news_sources}")
9. PONTOS POSITIVOS (ate 5 bullets)
10. RISCOS (ate 5 bullets - vacancia, inadimplência, juros, alavancagem)
11. PERSPECTIVA (3-4 frases, curto e medio prazo)

Use dados concretos. Comente sobre cenario do fundo e alavancagem. Não faça recomendações de compra/venda."""


def build_deep_generic_prompt(analysis: dict, portfolio_analysis: dict = None) -> str:
    """Prompt aprofundado para RF e Fundos."""
    portfolio_ctx = _build_portfolio_context(analysis, portfolio_analysis)
    news = analysis.get("news", [])
    news_text = _build_news_text(news)
    news_sources = _get_news_sources(news)
    tipo = analysis.get("tipo", "")

    # Para Fundos, incluir mais contexto
    is_fundo = tipo == "Fundo"

    extra_sections = ""
    if is_fundo:
        extra_sections = f"""2. CENARIO DO FUNDO (descreva o que o fundo faz, estrategia de gestao, tipo de ativos, gestora responsavel, posição no mercado)
3. ENDIVIDAMENTO E ALAVANCAGEM (o fundo utiliza alavancagem? Qual o nivel de risco? Qualidade dos ativos na carteira do fundo?)
4. DESEMPENHO vs CDI (esta acima ou abaixo? por que isso importa?)
5. IMPORTANCIA ESTRATEGICA (papel deste ativo no portfolio, contribuicao para diversificacao)
6. RESUMO DE NOTICIAS (faça um RESUMO das notícias recentes sobre o fundo/gestora, baseado nas manchetes e no seu conhecimento. Ao final escreva: "Ultimas notícias resumidas a partir de: {news_sources}")
7. PONTOS POSITIVOS (ate 4 bullets)
8. PONTOS DE ATENCAO (ate 4 bullets)
9. PERSPECTIVA (2-3 frases, curto e medio prazo)"""
    else:
        extra_sections = f"""2. DESEMPENHO vs CDI (esta acima ou abaixo? por que isso importa?)
3. IMPORTANCIA ESTRATEGICA (papel deste ativo no portfolio, contribuicao para diversificacao)
4. PONTOS POSITIVOS (ate 3 bullets)
5. PONTOS DE ATENCAO (ate 3 bullets)
6. PERSPECTIVA (2-3 frases)"""

    news_block = ""
    if news and is_fundo:
        news_block = f"\nMANCHETES DE NOTICIAS RECENTES:\n{news_text}"

    return f"""Você e um analista de investimentos brasileiro. Análise o ativo abaixo
de forma detalhada e profissional em portugues.

ATIVO: {analysis['nome']}
TIPO: {analysis['tipo']}
SETOR: {analysis.get('fundamentals', {}).get('setor', 'N/D')}

DADOS DA CARTEIRA:
- Saldo bruto: R$ {analysis['saldo_bruto']:,.2f}
- Alocacao: {analysis['alocacao']:.2f}%
- Rentabilidade mes: {analysis['rent_mes']:.2f}%
- %CDI mes: {analysis['cdi_mes']:.2f}%
- Rentabilidade ano: {analysis['rent_ano']:.2f}%
- %CDI ano: {analysis['cdi_ano']:.2f}%
{portfolio_ctx}
{news_block}

Forneça análise detalhada e estruturada:
1. RESUMO (3-4 frases sobre desempenho e papel na carteira)
{extra_sections}

Use dados concretos. Seja objetivo. Não faça recomendações de compra/venda."""


# ============================================================
# PROMPT DE SETOR - Análise setorial
# ============================================================

def build_sector_prompt(sector_name: str, sector_assets: list, macro: dict) -> str:
    """Prompt para análise setorial consolidada.

    Args:
        sector_name: Nome do setor
        sector_assets: Lista de ativos do setor com dados
        macro: Dados macroeconômicos
    """
    assets_text = ""
    for a in sector_assets:
        line = f"  - {a.get('ticker', 'N/D')}: R$ {a.get('saldo_bruto', 0):,.2f} ({a.get('alocacao', 0):.1f}%), Mês: {a.get('rent_mes', 0):+.2f}%, Ano: {a.get('rent_ano', 0):+.2f}%"
        assets_text += line + "\n"

    total_saldo = sum(a.get("saldo_bruto", 0) for a in sector_assets)
    total_aloc = sum(a.get("alocacao", 0) for a in sector_assets)

    return f"""Você e um analista de investimentos brasileiro experiente.
Faça uma análise BREVE do setor abaixo no contexto de uma carteira de investimentos. Escreva em portugues.

SETOR: {sector_name}
ALOCACAO TOTAL NO SETOR: {total_aloc:.1f}% (R$ {total_saldo:,.2f})
NUMERO DE ATIVOS: {len(sector_assets)}

ATIVOS DO SETOR:
{assets_text}
CENARIO MACRO:
- CDI anual: {macro.get('cdi_anual', 'N/D')}%
- SELIC meta: {macro.get('selic_meta', 'N/D')}%
- IPCA mensal: {macro.get('ipca_mensal', 'N/D')}%

Forneça em 2-3 paragrafos concisos:
1. Panorama atual do setor e perspectivas
2. Performance dos ativos do setor nesta carteira
3. Pontos de atencao e oportunidades

Seja objetivo e direto. Não faça recomendações de compra/venda."""


# ============================================================
# PROMPT DE EXECUÇÃO - Relatório de Ação
# ============================================================

def build_execution_prompt(portfolio_analysis: dict, asset_analyses: list, macro: dict) -> str:
    """Prompt para relatório de execução: diagnóstico + recomendações + tabela de ações.

    Args:
        portfolio_analysis: Análise consolidada da carteira (HHI, setores, top/piores, etc.)
        asset_analyses: Lista de análises individuais por ativo
        macro: Dados macroeconômicos (CDI, SELIC, IPCA)
    """
    # Distribuição por tipo
    tipo_dist = portfolio_analysis.get("distribuição_tipo", {})
    tipo_text = "\n".join(
        f"  - {k}: {v['count']} ativos, R$ {v['saldo']:,.2f} ({v['alocacao']:.1f}%)"
        for k, v in tipo_dist.items()
    )

    # Distribuição por setor
    setor_dist = portfolio_analysis.get("distribuição_setor", {})
    setor_text = "\n".join(
        f"  - {s}: {d['count']} ativo(s), {d['alocacao']:.1f}%, Mês: {d['rent_mes_ponderada']:+.2f}%, Ano: {d['rent_ano_ponderada']:+.2f}%"
        for s, d in setor_dist.items()
    )

    # Top e piores performers
    top = portfolio_analysis.get("top_performers_mes", [])
    top_text = "\n".join(f"  - {t['ticker']}: {t['rent']:+.2f}%" for t in top[:5])

    piores = portfolio_analysis.get("piores_mes", [])
    piores_text = "\n".join(f"  - {t['ticker']}: {t['rent']:+.2f}%" for t in piores[:5])

    # Lista completa de ativos com flags de risco
    ativos_lines = []
    for a in asset_analyses:
        ticker = a.get("ticker", "N/D")
        tipo = a.get("tipo", "")
        saldo = a.get("saldo_bruto", 0)
        aloc = a.get("alocacao", 0)
        rent_mes = a.get("rent_mes", 0)
        rent_ano = a.get("rent_ano", 0)
        fund = a.get("fundamentals", {})

        flags = []
        vol = fund.get("volatilidade")
        if vol is not None and vol > 40:
            flags.append(f"VOL_ALTA({vol:.0f}%)")
        if aloc > 15:
            flags.append(f"CONCENTRADO({aloc:.1f}%)")
        dl_ebitda = fund.get("divida_líquida_ebitda")
        if dl_ebitda is not None and dl_ebitda > 3:
            flags.append(f"ALAVANCADO(DL/EBITDA={dl_ebitda:.1f})")
        if rent_ano < -10:
            flags.append(f"QUEDA_ANO({rent_ano:+.1f}%)")
        if rent_mes < -5:
            flags.append(f"QUEDA_MES({rent_mes:+.1f}%)")

        dy = fund.get("dividend_yield")
        p_l = fund.get("p_l")

        flag_str = " [" + ", ".join(flags) + "]" if flags else ""
        extras = []
        if dy is not None:
            extras.append(f"DY={dy:.1f}%")
        if p_l is not None:
            extras.append(f"P/L={p_l:.1f}")
        extras_str = " (" + ", ".join(extras) + ")" if extras else ""

        line = f"  - {ticker} [{tipo}]: R$ {saldo:,.2f}, Aloc={aloc:.1f}%, Mês={rent_mes:+.2f}%, Ano={rent_ano:+.2f}%{extras_str}{flag_str}"
        ativos_lines.append(line)

    ativos_text = "\n".join(ativos_lines)

    return f"""Você e um consultor de investimentos senior brasileiro. Com base nos dados completos da carteira abaixo, elabore um RELATÓRIO DE EXECUÇÃO focado em AÇÕES CONCRETAS.

CARTEIRA:
- Patrimônio total: R$ {portfolio_analysis['total_bruto']:,.2f}
- Número de ativos: {portfolio_analysis['num_ativos']}
- Rentabilidade ponderada mes: {portfolio_analysis['rent_mes_ponderada']:+.2f}%
- Rentabilidade ponderada ano: {portfolio_analysis['rent_ano_ponderada']:+.2f}%
- Concentração (HHI): {portfolio_analysis['concentração_hhi']:.0f} ({portfolio_analysis['nivel_concentração']})

DISTRIBUICAO POR TIPO:
{tipo_text}

DISTRIBUICAO POR SETOR:
{setor_text}

MELHORES DO MES:
{top_text}

PIORES DO MES:
{piores_text}

CENARIO MACRO:
- CDI anual: {macro.get('cdi_anual', 'N/D')}%
- SELIC meta: {macro.get('selic_meta', 'N/D')}%
- IPCA mensal: {macro.get('ipca_mensal', 'N/D')}%

LISTA COMPLETA DE ATIVOS (com flags de risco):
{ativos_text}

Forneça o relatório de execução com EXATAMENTE 3 seções:

**1. DIAGNOSTICO**
- Situacao geral da carteira em 3-5 frases
- Liste 3-5 riscos principais identificados (concentração, alavancagem, volatilidade, performance negativa, exposição setorial excessiva)
- Compare performance da carteira vs CDI

**2. RECOMENDAÇÕES**
- 5-7 ações concretas e especificas para o assessor executar
- Para cada recomendacao: descreva a acao, justificativa e nivel de urgencia (ALTA/MEDIA/BAIXA)
- Foque em: redistribuição de posicoes, mitigacao de riscos, aumento de rentabilidade, diversificacao

**3. TABELA DE AÇÕES**
Para CADA ativo da carteira, forneca:
- Ticker
- Acao recomendada: MANTER, REDUZIR, AUMENTAR, MONITORAR ou SAIDA
- Justificativa (1 frase)
- Prioridade: ALTA, MEDIA ou BAIXA

Seja direto, objetivo e pratico. Use dados concretos. Este relatório e para o ASSESSOR executar ações, não para o cliente final."""


# ============================================================
# PROMPT DE IMPACTO DAS NOTICIAS NA CARTEIRA
# ============================================================

def build_news_impact_prompt(news_articles: list, portfolio_analysis: dict, asset_analyses: list, macro: dict) -> str:
    """Prompt para analisar impacto das notícias na carteira.

    Args:
        news_articles: Lista de notícias (título, categoria, fonte, data)
        portfolio_analysis: Análise consolidada da carteira
        asset_analyses: Lista de análises individuais por ativo
        macro: Dados macroeconômicos
    """
    news_lines = []
    for n in news_articles[:40]:
        cat = n.get("categoria", "")
        fonte = n.get("fonte", "")
        título = n.get("título", "")
        data = n.get("data", "")
        news_lines.append(f"  - [{cat}] {título} (Fonte: {fonte} | {data})")
    news_text = "\n".join(news_lines) if news_lines else "Nenhuma noticia disponível."

    ativos_lines = []
    for a in asset_analyses:
        ticker = a.get("ticker", "N/D")
        tipo = a.get("tipo", "")
        aloc = a.get("alocacao", 0)
        setor = a.get("fundamentals", {}).get("setor", "N/D")
        rent_mes = a.get("rent_mes", 0)
        rent_ano = a.get("rent_ano", 0)
        saldo = a.get("saldo_bruto", 0)
        ativos_lines.append(
            f"  - {ticker} [{tipo}] - Setor: {setor}, Aloc: {aloc:.1f}%, "
            f"Saldo: R$ {saldo:,.2f}, Mes: {rent_mes:+.2f}%, Ano: {rent_ano:+.2f}%"
        )
    ativos_text = "\n".join(ativos_lines)

    setor_dist = portfolio_analysis.get("distribuição_setor", {})
    setor_lines = []
    for s, d in setor_dist.items():
        ativos_setor = d.get("ativos", [])
        ativos_str = ", ".join(ativos_setor) if isinstance(ativos_setor, list) else str(ativos_setor)
        setor_lines.append(
            f"  - {s}: {d['alocacao']:.1f}% (Ativos: {ativos_str})"
        )
    setor_text = "\n".join(setor_lines)

    tipo_dist = portfolio_analysis.get("distribuição_tipo", {})
    tipo_text = "\n".join(
        f"  - {k}: {v['count']} ativos, R$ {v.get('saldo', 0):,.2f} ({v['alocacao']:.1f}%)"
        for k, v in tipo_dist.items()
    )

    concentracao = portfolio_analysis.get("nivel_concentração", "N/D")
    hhi = portfolio_analysis.get("concentração_hhi", 0)

    return f"""Você e um estrategista-chefe de investimentos de uma assessoria premium brasileira. Sua missão e produzir uma ANÁLISE DE IMPACTO PROFUNDA e ESTRATEGICA, conectando as noticias do momento com a carteira real do cliente. Escreva em portugues.

IMPORTANTE: Não seja generico. Cada afirmação DEVE estar conectada a uma noticia especifica OU a um ativo especifico da carteira. Use raciocinio de CAUSA e EFEITO.

═══════════════════════════════════════
CARTEIRA DO CLIENTE
═══════════════════════════════════════
- Patrimônio total: R$ {portfolio_analysis['total_bruto']:,.2f}
- Número de ativos: {portfolio_analysis['num_ativos']}
- Rent. mes ponderada: {portfolio_analysis['rent_mes_ponderada']:+.2f}%
- Rent. ano ponderada: {portfolio_analysis['rent_ano_ponderada']:+.2f}%
- Concentracao: {concentracao} (HHI: {hhi:.4f})

DISTRIBUICAO POR TIPO:
{tipo_text}

ATIVOS DA CARTEIRA (com dados recentes):
{ativos_text}

DISTRIBUICAO SETORIAL (com ativos por setor):
{setor_text}

CENARIO MACRO ATUAL:
- CDI anual: {macro.get('cdi_anual', 'N/D')}%
- SELIC meta: {macro.get('selic_meta', 'N/D')}%
- IPCA mensal: {macro.get('ipca_mensal', 'N/D')}%

NOTICIAS RECENTES (leia TODAS com atencao):
{news_text}

═══════════════════════════════════════
INSTRUÇÕES DE ANÁLISE
═══════════════════════════════════════

Produza uma analise com EXATAMENTE 8 secoes. Cada secao deve ser rica, profunda e com topicos organizados. NAO seja superficial.

**1. CONTEXTO MACROECONOMICO E POLITICO**
Construa o CENARIO COMPLETO do momento atual baseado nas noticias. Organize em topicos:

- **Politica Monetaria e Juros**: O que esta acontecendo com SELIC, juros futuros, expectativas do COPOM? Como isso se conecta as noticias? Qual a tendencia?
- **Inflacao e Poder de Compra**: IPCA, IGP-M, pressoes inflacionarias ou deflacionarias identificadas nas noticias. Impacto no consumo e renda fixa.
- **Cenario Fiscal e Politico**: Decisoes do governo, reformas, gastos publicos, arcabouco fiscal, risco politico. Cite noticias especificas.
- **Cenario Internacional**: Fed, BCE, juros globais, guerras comerciais, commodities, dolar. O que vem de fora e como afeta o Brasil?
- **Cambio e Fluxo de Capital**: Tendencia do dolar/real, entrada/saida de capital estrangeiro, balanca comercial.

Para cada topico, CITE pelo menos uma noticia especifica que sustenta sua analise. Use 10-15 frases no total. Seja analitico, nao apenas descritivo.

**2. MAPA DE IMPACTO SETORIAL**
Para CADA setor presente na carteira do cliente, analise:
- Quais noticias afetam diretamente este setor (positiva ou negativamente)?
- Qual a TENDENCIA do setor no curto prazo (1-3 meses) baseado no cenario?
- Nivel de exposicao do cliente ao setor (% da carteira)
- Classificacao: FAVORAVEL / NEUTRO / DESFAVORAVEL

Formato por setor:
**[Nome do Setor]** (X% da carteira - Ativos: TICK1, TICK2)
- Impacto: [FAVORAVEL/NEUTRO/DESFAVORAVEL]
- Analise: [2-3 frases conectando noticias ao setor]
- Noticias relacionadas: "[titulo da noticia 1]", "[titulo da noticia 2]"

**3. ATIVOS EM RISCO**
Liste os ativos da carteira que podem ser NEGATIVAMENTE impactados. Para cada:
- **Ticker**: nome e tipo do ativo
- **Risco**: ALTO / MEDIO / BAIXO
- **Exposicao**: quanto representa na carteira (% e R$)
- **Cadeia de Impacto**: explique a LOGICA completa: Noticia -> Efeito no setor/economia -> Impacto no ativo especifico
- **Noticia-gatilho**: "Conforme noticia '[titulo exato]'..."
- **Sinal de Alerta**: o que monitorar para confirmar se o risco se materializa

Se nenhum ativo estiver em risco, diga explicitamente e justifique.

**4. ATIVOS FAVORECIDOS**
Liste os ativos que podem ser POSITIVAMENTE impactados. Para cada:
- **Ticker**: nome e tipo do ativo
- **Potencial**: ALTO / MEDIO / BAIXO
- **Exposicao**: quanto representa na carteira (% e R$)
- **Cadeia de Oportunidade**: Noticia -> Efeito positivo -> Beneficio para o ativo
- **Noticia-catalisador**: "Conforme noticia '[titulo exato]'..."
- **Janela de Oportunidade**: por quanto tempo este catalisador deve persistir?

Se nenhum for favorecido, diga explicitamente e justifique.

**5. CENARIOS PROSPECTIVOS**
Construa 3 cenarios de curto prazo (1-3 meses) baseados nas tendencias das noticias:

- **Cenario Otimista (Bull Case)**: O que precisaria acontecer para a carteira performar bem? Quais noticias apontam nessa direcao? Probabilidade estimada.
- **Cenario Base (Mais Provavel)**: O que PROVAVELMENTE vai acontecer dado o cenario atual? Como a carteira se comportaria? Probabilidade estimada.
- **Cenario Pessimista (Bear Case)**: Quais riscos podem se materializar? Quais noticias sinalizam perigo? Qual seria o impacto na carteira? Probabilidade estimada.

Para cada cenario, estime o impacto aproximado na rentabilidade da carteira (ex: "poderia adicionar +1-2% no mes" ou "risco de queda de -3-5%").

**6. TERMOMETRO DE RISCO DA CARTEIRA**
Avaliacao consolidada do nivel de risco ATUAL da carteira frente ao cenario:
- **Nivel Geral de Risco**: BAIXO / MODERADO / ELEVADO / CRITICO
- **Principais Vulnerabilidades**: liste os 3 maiores pontos fracos da carteira no cenario atual
- **Fatores de Protecao**: o que na carteira serve como protecao/hedge natural?
- **Diversificacao**: a carteira esta bem posicionada para o cenario? Faltam setores defensivos? Ha concentracao excessiva em algum segmento vulneravel?
- **Indice de Urgencia**: de 1 a 10, qual a urgencia de agir sobre a carteira agora? Justifique.

**7. ACOES RECOMENDADAS**
5-7 acoes concretas e priorizadas que o assessor deveria executar. Para cada:
- **Acao**: descricao objetiva do que fazer
- **Justificativa**: por que fazer isso AGORA (conecte a noticia/cenario)
- **Prioridade**: CRITICA / ALTA / MEDIA / BAIXA
- **Horizonte**: IMEDIATO (hoje) / CURTO PRAZO (1-2 semanas) / MEDIO PRAZO (1-3 meses)
- **Impacto Esperado**: o que se espera ganhar/proteger com essa acao

Ordene da mais urgente para a menos urgente.

**8. RESUMO EXECUTIVO**
5-8 frases de alto nivel para o assessor ter uma visao rapida:
- Qual o "tom" geral do mercado para esta carteira? (otimista/cauteloso/defensivo)
- Os 2-3 principais riscos que merecem atencao imediata
- As 2-3 maiores oportunidades identificadas
- Uma frase final de recomendacao estrategica geral

Tom: profissional, analitico, direto, sem alarmismo mas sem omitir riscos reais.

═══════════════════════════════════════
REGRAS FINAIS
═══════════════════════════════════════
- SEMPRE cite titulos de noticias entre aspas simples quando referenciar
- Use raciocinio de CAUSA e EFEITO, nao apenas liste fatos
- Conecte CADA ponto a dados concretos (noticias, tickers, percentuais)
- Seja ANALITICO: explique o POR QUE, nao apenas o QUE
- Nao repita informacoes entre secoes — cada secao traz perspectiva UNICA"""


# ============================================================
# PROMPT DE RECOMENDAÇÕES DE MIGRACAO
# ============================================================

def build_migration_prompt(
    portfolio_analysis: dict,
    asset_analyses: list,
    macro: dict,
    news_impact_text: str = "",
) -> str:
    """Prompt para gerar recomendações de migração/rebalanceamento.

    Args:
        portfolio_analysis: Análise consolidada
        asset_analyses: Lista de análises individuais
        macro: Dados macro
        news_impact_text: (Opcional) Texto da análise de impacto de notícias
    """
    tipo_dist = portfolio_analysis.get("distribuição_tipo", {})
    tipo_text = "\n".join(
        f"  - {k}: {v['count']} ativos, R$ {v['saldo']:,.2f} ({v['alocacao']:.1f}%)"
        for k, v in tipo_dist.items()
    )

    setor_dist = portfolio_analysis.get("distribuição_setor", {})
    setor_text = "\n".join(
        f"  - {s}: {d['count']} ativo(s), {d['alocacao']:.1f}%, Mês: {d['rent_mes_ponderada']:+.2f}%"
        for s, d in setor_dist.items()
    )

    ativos_lines = []
    for a in asset_analyses:
        ticker = a.get("ticker", "N/D")
        tipo = a.get("tipo", "")
        saldo = a.get("saldo_bruto", 0)
        aloc = a.get("alocacao", 0)
        rent_mes = a.get("rent_mes", 0)
        rent_ano = a.get("rent_ano", 0)
        fund = a.get("fundamentals", {})

        extras = []
        dy = fund.get("dividend_yield")
        if dy is not None:
            extras.append(f"DY={dy:.1f}%")
        p_l = fund.get("p_l")
        if p_l is not None:
            extras.append(f"P/L={p_l:.1f}")
        dl = fund.get("divida_líquida_ebitda")
        if dl is not None:
            extras.append(f"DL/EBITDA={dl:.1f}")

        extras_str = " (" + ", ".join(extras) + ")" if extras else ""
        line = f"  - {ticker} [{tipo}]: R$ {saldo:,.2f}, Aloc={aloc:.1f}%, Mês={rent_mes:+.2f}%, Ano={rent_ano:+.2f}%{extras_str}"
        ativos_lines.append(line)
    ativos_text = "\n".join(ativos_lines)

    impact_block = ""
    risk_instruction = ""
    if news_impact_text:
        truncated = news_impact_text[:2500]
        impact_block = f"""
CONTEXTO ADICIONAL - IMPACTO DAS NOTICIAS:
{truncated}
"""
        risk_instruction = "IMPORTANTE: Todos os riscos identificados na análise de impacto acima DEVEM ter uma estrategia de mitigacao correspondente na secao 3."
    else:
        risk_instruction = "Sem contexto de noticias disponivel. Foque em riscos estruturais da carteira: concentracao excessiva, volatilidade alta, alavancagem, baixa diversificacao."

    return f"""Você e um consultor de investimentos senior brasileiro especializado em alocacao de ativos e rebalanceamento de carteiras. Análise a carteira e faça recomendações de MIGRACAO, MITIGACAO DE RISCOS e REBALANCEAMENTO. Escreva em portugues.

CARTEIRA:
- Patrimônio total: R$ {portfolio_analysis['total_bruto']:,.2f}
- Número de ativos: {portfolio_analysis['num_ativos']}
- Rent. ponderada mes: {portfolio_analysis['rent_mes_ponderada']:+.2f}%
- Rent. ponderada ano: {portfolio_analysis['rent_ano_ponderada']:+.2f}%
- Concentração (HHI): {portfolio_analysis['concentração_hhi']:.0f} ({portfolio_analysis['nivel_concentração']})

DISTRIBUICAO POR TIPO:
{tipo_text}

DISTRIBUICAO POR SETOR:
{setor_text}

CENARIO MACRO:
- CDI anual: {macro.get('cdi_anual', 'N/D')}%
- SELIC meta: {macro.get('selic_meta', 'N/D')}%
- IPCA: {macro.get('ipca_mensal', 'N/D')}%

ATIVOS (com indicadores):
{ativos_text}
{impact_block}
{risk_instruction}

Forneça recomendações com EXATAMENTE 5 seções:

**1. DIAGNOSTICO DA ALOCACAO**
- Avalie a distribuição atual por tipo e setor
- Compare com alocacao ideal para perfil moderado/agressivo
- Identifique desequilibrios (concentração excessiva, falta de diversificacao, exposição a riscos)

**2. RECOMENDAÇÕES DE MIGRACAO**
- 5-8 recomendações concretas de migração
- Para cada: ativo de ORIGEM -> tipo de ativo de DESTINO sugerido, justificativa, urgencia (ALTA/MEDIA/BAIXA)
- Foque em: reduzir concentração, melhorar diversificacao, otimizar retorno/risco

**3. ESTRATEGIAS DE MITIGACAO**
Para cada risco identificado (do impacto das noticias OU riscos estruturais da carteira):
- **Risco**: descricao clara do risco
- **Como mitigar**: acao concreta para reduzir/eliminar o risco
- **Ativos afetados**: quais tickers sao impactados
- **Urgencia**: ALTA / MEDIA / BAIXA
Liste pelo menos 3-5 estrategias de mitigacao. Priorize riscos de maior urgencia.

**4. TABELA RESUMO POR ATIVO**
Para CADA ativo da carteira:
- Ticker | Acao (MANTER/MIGRAR/REDUZIR/AUMENTAR) | Destino sugerido | Justificativa | Prioridade

**5. ALOCACAO ALVO SUGERIDA**
- Distribuição ideal por tipo (%) considerando o cenario macro atual
- Distribuição ideal por setor (%) se aplicavel
- Justifique brevemente a alocacao sugerida

Seja pratico e objetivo. Considere custos de transação e tributação ao recomendar migrações. Este relatório e para o ASSESSOR executar ações."""


# ============================================================
# PROMPT DE RESUMO DIARIO DE NOTICIAS
# ============================================================

def build_daily_summary_prompt(news_articles: list) -> str:
    """Prompt para resumo diario focado em Geopolítica, AI e Economia.

    Mantido para retrocompatibilidade. Internamente usa build_period_summary_prompt().
    """
    return build_period_summary_prompt(news_articles, "diario")


def build_period_summary_prompt(news_articles: list, period: str = "diario") -> str:
    """Prompt para resumo por periodo focado em Geopolítica, AI e Economia.

    Args:
        news_articles: Lista de noticias (titulo, categoria, fonte, data)
        period: "diario" | "semanal" | "mensal"
    """
    # Limites por periodo
    config = {
        "diario": {
            "limit": 40,
            "label": "DIARIO",
            "header": "NOTICIAS DO DIA",
            "geo_frases": "3-4 frases",
            "ai_frases": "3-4 frases",
            "eco_frases": "3-4 frases",
            "instrucao_extra": "Seja direto, objetivo e use linguagem profissional. Não use emojis. Cada secao deve ter 3-4 frases densas e informativas.",
        },
        "semanal": {
            "limit": 50,
            "label": "SEMANAL",
            "header": "NOTICIAS DA SEMANA",
            "geo_frases": "5-6 frases",
            "ai_frases": "5-6 frases",
            "eco_frases": "5-6 frases",
            "instrucao_extra": "Identifique TENDENCIAS da semana — o que se repetiu, o que mudou de direcao, o que ganhou forca. Conecte eventos entre si quando possivel. Cada secao deve ter 5-6 frases densas e analiticas.",
        },
        "mensal": {
            "limit": 60,
            "label": "MENSAL",
            "header": "NOTICIAS DO MES",
            "geo_frases": "6-8 frases",
            "ai_frases": "6-8 frases",
            "eco_frases": "6-8 frases",
            "instrucao_extra": "Foque em MOVIMENTOS ESTRUTURAIS e mudancas de ciclo. Identifique tendencias macro que persistiram ao longo do mes. Analise implicacoes de medio/longo prazo para investidores. Cada secao deve ter 6-8 frases com visao macro e analitica.",
        },
    }

    cfg = config.get(period, config["diario"])

    news_lines = []
    for n in news_articles[:cfg["limit"]]:
        cat = n.get("categoria", "")
        fonte = n.get("fonte", "")
        título = n.get("título", "")
        news_lines.append(f"  - [{cat}] {título} ({fonte})")
    news_text = "\n".join(news_lines) if news_lines else "Nenhuma noticia disponível."

    return f"""Você e um analista senior de mercado financeiro brasileiro. Com base nas notícias abaixo, escreva um RESUMO {cfg['label']} conciso e profissional em portugues.

{cfg['header']}:
{news_text}

Estruture o resumo em EXATAMENTE 3 seções com os títulos abaixo (use exatamente este formato):

**GEOPOLITICA**
Resuma em {cfg['geo_frases']} os principais eventos geopolíticos que podem afetar mercados e investimentos. Inclua tensoes internacionais, acordos comerciais, política externa, conflitos, sanções. Se não houver notícias geopolíticas relevantes, mencione o cenario global atual brevemente.

**INTELIGENCIA ARTIFICIAL**
Resuma em {cfg['ai_frases']} os avancos, regulações e impactos de IA nos mercados. Inclua lançamentos de modelos, regulações, impacto em setores, empresas de tecnologia. Se não houver notícias de IA, comente brevemente o panorama atual do setor.

**ECONOMIA**
Resuma em {cfg['eco_frases']} o cenario economico brasileiro e global. Inclua dados de inflacao, juros, cambio, PIB, emprego, política fiscal/monetaria. Foque no que e mais relevante para investidores.

{cfg['instrucao_extra']}
Não use emojis. Use linguagem profissional."""
