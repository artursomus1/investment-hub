"""Registro de mudanças nas carteiras - persistencia JSON."""

import json
import uuid
from dataclasses import dataclass, asdict, field
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from agente_investimentos.config import PASTA_SAIDA

PASTA_MUDANCAS = PASTA_SAIDA / "registro_mudanças"
PASTA_MUDANCAS.mkdir(parents=True, exist_ok=True)

AÇÕES_VALIDAS = ["COMPRA", "VENDA", "AUMENTO", "REDUCAO", "MIGRACAO"]


@dataclass
class ChangeRecord:
    """Registro de uma mudanca na carteira."""
    change_id: str
    timestamp: str
    data_mudanca: str
    client_code: str
    ticker: str
    acao: str
    quantidade: float
    valor: float
    motivacao: str
    recomendacao_ref: str = ""


def _new_id() -> str:
    return uuid.uuid4().hex[:12]


def save_change(
    data_mudanca: str,
    client_code: str,
    ticker: str,
    acao: str,
    quantidade: float,
    valor: float,
    motivacao: str,
    recomendacao_ref: str = "",
) -> ChangeRecord:
    """Cria e salva um novo registro de mudanca."""
    record = ChangeRecord(
        change_id=_new_id(),
        timestamp=datetime.now().isoformat(),
        data_mudanca=data_mudanca,
        client_code=client_code.strip().upper(),
        ticker=ticker.strip().upper(),
        acao=acao.upper(),
        quantidade=quantidade,
        valor=valor,
        motivacao=motivacao.strip(),
        recomendacao_ref=recomendacao_ref.strip(),
    )
    path = PASTA_MUDANCAS / f"{record.change_id}.json"
    path.write_text(
        json.dumps(asdict(record), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return record


def load_all_changes() -> List[ChangeRecord]:
    """Carrega todos os registros, mais recente primeiro."""
    records = []
    for f in sorted(PASTA_MUDANCAS.glob("*.json"), reverse=True):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            records.append(ChangeRecord(**data))
        except Exception:
            continue
    # Ordena por timestamp decrescente
    records.sort(key=lambda r: r.timestamp, reverse=True)
    return records


def filter_changes(
    records: List[ChangeRecord],
    client_code: Optional[str] = None,
    ticker: Optional[str] = None,
    acao: Optional[str] = None,
    data_inicio: Optional[str] = None,
    data_fim: Optional[str] = None,
) -> List[ChangeRecord]:
    """Filtra registros por critérios."""
    filtered = records
    if client_code:
        filtered = [r for r in filtered if r.client_code == client_code.upper()]
    if ticker:
        filtered = [r for r in filtered if r.ticker == ticker.upper()]
    if acao:
        filtered = [r for r in filtered if r.acao == acao.upper()]
    if data_inicio:
        filtered = [r for r in filtered if r.data_mudanca >= data_inicio]
    if data_fim:
        filtered = [r for r in filtered if r.data_mudanca <= data_fim]
    return filtered


def get_change_metrics(records: List[ChangeRecord]) -> dict:
    """Calcula métricas agregadas dos registros."""
    if not records:
        return {
            "total": 0,
            "compras": 0,
            "vendas": 0,
            "aumentos": 0,
            "reducoes": 0,
            "migrações": 0,
            "valor_total": 0.0,
            "clientes_únicos": 0,
            "tickers_únicos": 0,
        }

    return {
        "total": len(records),
        "compras": sum(1 for r in records if r.acao == "COMPRA"),
        "vendas": sum(1 for r in records if r.acao == "VENDA"),
        "aumentos": sum(1 for r in records if r.acao == "AUMENTO"),
        "reducoes": sum(1 for r in records if r.acao == "REDUCAO"),
        "migrações": sum(1 for r in records if r.acao == "MIGRACAO"),
        "valor_total": sum(r.valor for r in records),
        "clientes_únicos": len(set(r.client_code for r in records)),
        "tickers_únicos": len(set(r.ticker for r in records)),
    }


def delete_change(change_id: str) -> bool:
    """Exclui um registro pelo ID."""
    path = PASTA_MUDANCAS / f"{change_id}.json"
    if path.exists():
        path.unlink()
        return True
    return False
