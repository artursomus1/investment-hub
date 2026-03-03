"""Modelos de dados para ativos extraídos do PDF."""

from dataclasses import dataclass, field
from typing import List


@dataclass
class RawAsset:
    """Ativo bruto extraído do PDF (strings originais)."""
    nome: str
    saldo_bruto: str
    quantidade: str
    alocacao: str
    rent_mes: str
    cdi_mes: str
    rent_ano: str
    cdi_ano: str


@dataclass
class ParsedAsset:
    """Ativo com valores numéricos parseados."""
    nome: str
    ticker: str  # extraído do nome (ex: PETR4, KNRI11)
    saldo_bruto: float
    quantidade: float
    alocacao: float  # percentual
    rent_mes: float
    cdi_mes: float
    rent_ano: float
    cdi_ano: float
    tipo: str = ""  # preenchido pelo classifier: Acao, FII, RF, Fundo


@dataclass
class PortfolioData:
    """Dados completos da carteira extraída do PDF."""
    client_code: str
    pdf_filename: str
    assets: List[ParsedAsset] = field(default_factory=list)
    total_bruto: float = 0.0
    data_referencia: str = ""

    @property
    def num_assets(self) -> int:
        return len(self.assets)
