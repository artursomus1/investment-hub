"""Extrator de dados do PDF XP Performance usando regex do leitor original."""

import re
from pathlib import Path
from typing import List, Optional

import pdfplumber

from agente_investimentos.pdf_reader.models import RawAsset, ParsedAsset, PortfolioData
from agente_investimentos.utils.formatters import parse_br_number, parse_percent_str, extract_client_code
from agente_investimentos.utils.exceptions import PDFExtractionError

# Regex original do LEITOR XP PERFORMANCE.PY
PADRAO_LINHA = re.compile(
    r"^(.*?)\s+R\$\s?([\d\.,]+)\s+([-\d\.]+)\s+([\d\.,]+%)\s+([-\d\.,]+%)\s+([-\d\.,]+%)\s+([-\d\.,]+%)\s+([-\d\.,]+%)"
)

# Regex para extrair ticker do nome do ativo
PADRAO_TICKER = re.compile(r"\b([A-Z]{4}\d{1,2})\b")

# Regex para data de referência
PADRAO_DATA_REF = re.compile(r"Ref[.\s]*(\d{2}[./]\d{2}(?:[./]\d{2,4})?)")


def _extract_ticker(nome: str) -> str:
    """Extrai ticker de ações/FIIs do nome do ativo."""
    match = PADRAO_TICKER.search(nome.upper())
    if match:
        return match.group(1)
    # Para RF e fundos, usa o nome limpo como identificador
    return nome.strip()


def _extract_ref_date(filename: str) -> str:
    """Extrai data de referência do nome do arquivo."""
    match = PADRAO_DATA_REF.search(filename)
    return match.group(1) if match else ""


def extract_raw_assets(pdf_path: Path) -> List[RawAsset]:
    """Extrai ativos brutos do PDF, pulando páginas 0-1 e linhas de estratégia."""
    assets = []
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages[2:]:  # Pula capa e sumário
                texto = page.extract_text()
                if not texto:
                    continue
                for linha in texto.split("\n"):
                    linha = linha.strip()
                    match = PADRAO_LINHA.match(linha)
                    if not match:
                        continue
                    qtd = match.group(3)
                    if qtd == "-":  # Ignora linhas de estratégia
                        continue
                    assets.append(RawAsset(
                        nome=match.group(1).strip(),
                        saldo_bruto=match.group(2),
                        quantidade=qtd,
                        alocacao=match.group(4),
                        rent_mes=match.group(5),
                        cdi_mes=match.group(6),
                        rent_ano=match.group(7),
                        cdi_ano=match.group(8),
                    ))
    except Exception as e:
        raise PDFExtractionError(f"Erro ao ler {pdf_path.name}: {e}") from e
    return assets


def parse_assets(raw_assets: List[RawAsset]) -> List[ParsedAsset]:
    """Converte ativos brutos em ativos parseados com valores numéricos."""
    parsed = []
    for raw in raw_assets:
        parsed.append(ParsedAsset(
            nome=raw.nome,
            ticker=_extract_ticker(raw.nome),
            saldo_bruto=parse_br_number(raw.saldo_bruto),
            quantidade=parse_br_number(raw.quantidade),
            alocacao=parse_percent_str(raw.alocacao),
            rent_mes=parse_percent_str(raw.rent_mes),
            cdi_mes=parse_percent_str(raw.cdi_mes),
            rent_ano=parse_percent_str(raw.rent_ano),
            cdi_ano=parse_percent_str(raw.cdi_ano),
        ))
    return parsed


def extract_portfolio(pdf_path: Path) -> PortfolioData:
    """Pipeline completo: extrai e parseia todos os ativos do PDF."""
    filename = pdf_path.name
    client_code = extract_client_code(filename)
    ref_date = _extract_ref_date(filename)

    raw = extract_raw_assets(pdf_path)
    parsed = parse_assets(raw)

    total = sum(a.saldo_bruto for a in parsed)

    return PortfolioData(
        client_code=client_code,
        pdf_filename=filename,
        assets=parsed,
        total_bruto=total,
        data_referencia=ref_date,
    )


def find_pdf(pasta: Optional[Path] = None) -> Path:
    """Encontra o primeiro PDF XP Performance na pasta de coleta."""
    from agente_investimentos.config import PASTA_PDFS
    pasta = pasta or PASTA_PDFS
    pdfs = list(pasta.glob("*.pdf"))
    if not pdfs:
        raise PDFExtractionError(f"Nenhum PDF encontrado em {pasta}")
    return pdfs[0]
