"""Persistencia de histórico de execuções em JSON."""

import json
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from agente_investimentos.config import PASTA_SAIDA

PASTA_HISTORICO = PASTA_SAIDA / "histórico"
PASTA_HISTORICO.mkdir(parents=True, exist_ok=True)


@dataclass
class RunRecord:
    """Registro resumido de uma execução."""
    run_id: str
    timestamp: str
    client_code: str
    total_bruto: float
    num_ativos: int
    rent_mes_ponderada: float
    rent_ano_ponderada: float
    nivel_concentração: str
    concentração_hhi: float
    detailed_pdf: str
    execution_pdf: str
    elapsed: float


def save_run(result: Dict[str, Any]) -> RunRecord:
    """Salva um registro de execução a partir do dict retornado por run()."""
    portfolio = result["portfolio"]
    pa = result["portfolio_analysis"]
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_id = f"{portfolio.client_code}_{ts}"

    record = RunRecord(
        run_id=run_id,
        timestamp=datetime.now().isoformat(),
        client_code=portfolio.client_code,
        total_bruto=portfolio.total_bruto,
        num_ativos=portfolio.num_assets,
        rent_mes_ponderada=pa.get("rent_mes_ponderada", 0),
        rent_ano_ponderada=pa.get("rent_ano_ponderada", 0),
        nivel_concentração=pa.get("nivel_concentração", ""),
        concentração_hhi=pa.get("concentração_hhi", 0),
        detailed_pdf=str(result["detailed_path"]) if result.get("detailed_path") else "",
        execution_pdf=str(result["execution_path"]) if result.get("execution_path") else "",
        elapsed=result.get("elapsed", 0),
    )

    path = PASTA_HISTORICO / f"{run_id}.json"
    path.write_text(json.dumps(asdict(record), ensure_ascii=False, indent=2), encoding="utf-8")
    return record


def load_all_runs() -> List[RunRecord]:
    """Carrega todos os registros, mais recente primeiro."""
    records = []
    for f in sorted(PASTA_HISTORICO.glob("*.json"), reverse=True):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            records.append(RunRecord(**data))
        except Exception:
            continue
    return records


def load_run(run_id: str) -> Optional[RunRecord]:
    """Carrega um registro especifico pelo run_id."""
    path = PASTA_HISTORICO / f"{run_id}.json"
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return RunRecord(**data)
    except Exception:
        return None
