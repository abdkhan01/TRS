from __future__ import annotations

from pathlib import Path
from typing import Any

import duckdb


def sql_string(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def connect(db_path: Path, *, read_only: bool = False) -> duckdb.DuckDBPyConnection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return duckdb.connect(str(db_path), read_only=read_only)


def create_parquet_views(db_path: Path, records: list[dict[str, Any]]) -> list[str]:
    created: list[str] = []
    with connect(db_path) as con:
        for record in records:
            view_name = record["view_name"]
            parquet_path = Path(record["output_path"]).resolve()
            con.execute(
                f"""
                create or replace view "{view_name}" as
                select *
                from read_parquet({sql_string(str(parquet_path))})
                """
            )
            created.append(view_name)
        from trs.geo.reference import create_location_reference_tables

        create_location_reference_tables(con)
    return created


def list_views(db_path: Path) -> list[str]:
    with connect(db_path, read_only=True) as con:
        rows = con.execute(
            """
            select table_name
            from information_schema.tables
            where table_schema = 'main'
            order by table_name
            """
        ).fetchall()
    return [row[0] for row in rows]
