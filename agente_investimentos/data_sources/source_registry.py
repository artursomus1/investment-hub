"""Registro de todas as fontes de dados utilizadas na análise."""

from dataclasses import dataclass, field
from typing import List, Dict
import json
from pathlib import Path


@dataclass
class SourceEntry:
    """Uma fonte de dados consultada."""
    tipo: str          # "API", "RSS", "PDF"
    nome: str          # "brapi.dev", "BCB", "Google News"
    url: str           # URL consultada
    ticker: str = ""   # ticker relacionado (se aplicável)
    status: str = "ok" # "ok", "erro", "cache"


class SourceRegistry:
    """Registra todas as fontes consultadas para rastreabilidade."""

    def __init__(self):
        self.sources: List[SourceEntry] = []

    def add(self, tipo: str, nome: str, url: str, ticker: str = "", status: str = "ok"):
        self.sources.append(SourceEntry(
            tipo=tipo, nome=nome, url=url, ticker=ticker, status=status
        ))

    def to_list(self) -> List[Dict]:
        return [
            {"tipo": s.tipo, "nome": s.nome, "url": s.url, "ticker": s.ticker, "status": s.status}
            for s in self.sources
        ]

    def save(self, path: Path):
        """Salva registro de fontes em JSON."""
        path.write_text(
            json.dumps(self.to_list(), ensure_ascii=False, indent=2),
            encoding="utf-8"
        )

    @property
    def summary(self) -> str:
        ok = sum(1 for s in self.sources if s.status == "ok")
        cached = sum(1 for s in self.sources if s.status == "cache")
        err = sum(1 for s in self.sources if s.status == "erro")
        return f"Fontes: {ok} OK, {cached} cache, {err} erro(s) | Total: {len(self.sources)}"
