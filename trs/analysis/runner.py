from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from time import perf_counter
from typing import Any, Sequence

from trs.storage.duckdb import connect


@dataclass(frozen=True)
class QueryResult:
    rows: list[dict[str, Any]]
    runtime_ms: float


def run_query(
    db_path: Path,
    sql: str,
    parameters: Sequence[Any] = (),
) -> QueryResult:
    started = perf_counter()
    with connect(db_path, read_only=True) as con:
        cursor = con.execute(sql, list(parameters))
        columns = [item[0] for item in cursor.description]
        rows = [dict(zip(columns, row, strict=True)) for row in cursor.fetchall()]
    return QueryResult(rows=rows, runtime_ms=(perf_counter() - started) * 1000)
