"""Gerenciador de cache JSON com TTL por categoria."""

import json
import time
from pathlib import Path
from typing import Any, Optional

from agente_investimentos.config import (
    PASTA_CACHE,
    CACHE_TTL_FUNDAMENTALS,
    CACHE_TTL_DIVIDENDS,
    CACHE_TTL_MACRO,
    CACHE_TTL_NEWS_BROAD,
)

# TTL por categoria
_TTL_MAP = {
    "fundamentals": CACHE_TTL_FUNDAMENTALS,
    "dividends": CACHE_TTL_DIVIDENDS,
    "macro": CACHE_TTL_MACRO,
    "sector": CACHE_TTL_FUNDAMENTALS,
    "news": CACHE_TTL_MACRO,
    "news_broad": CACHE_TTL_NEWS_BROAD,
}


class CacheManager:
    """Cache baseado em arquivos JSON com TTL."""

    def __init__(self, base_dir: Optional[Path] = None):
        self.base_dir = base_dir or PASTA_CACHE

    def _get_path(self, category: str, key: str) -> Path:
        cat_dir = self.base_dir / category
        cat_dir.mkdir(parents=True, exist_ok=True)
        safe_key = key.replace("/", "_").replace("\\", "_")
        return cat_dir / f"{safe_key}.json"

    def _get_ttl(self, category: str) -> int:
        return _TTL_MAP.get(category, CACHE_TTL_FUNDAMENTALS)

    def is_valid(self, category: str, key: str) -> bool:
        """Verifica se o cache existe e não expirou."""
        path = self._get_path(category, key)
        if not path.exists():
            return False
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            ttl = self._get_ttl(category)
            return (time.time() - data.get("timestamp", 0)) < ttl
        except (json.JSONDecodeError, KeyError):
            return False

    def get(self, category: str, key: str) -> Optional[Any]:
        """Retorna dados do cache se válido, senão None."""
        if not self.is_valid(category, key):
            return None
        path = self._get_path(category, key)
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            return data.get("value")
        except (json.JSONDecodeError, KeyError):
            return None

    def set(self, category: str, key: str, value: Any) -> None:
        """Salva dados no cache com timestamp."""
        path = self._get_path(category, key)
        data = {
            "timestamp": time.time(),
            "key": key,
            "category": category,
            "value": value,
        }
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def clear(self, category: Optional[str] = None) -> int:
        """Limpa cache de uma categoria ou todo. Retorna número de arquivos removidos."""
        count = 0
        if category:
            cat_dir = self.base_dir / category
            if cat_dir.exists():
                for f in cat_dir.glob("*.json"):
                    f.unlink()
                    count += 1
        else:
            for cat_dir in self.base_dir.iterdir():
                if cat_dir.is_dir():
                    for f in cat_dir.glob("*.json"):
                        f.unlink()
                        count += 1
        return count
