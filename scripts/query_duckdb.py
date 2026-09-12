#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from trs.ingest.parquet_writer import read_manifest_lock
from trs.storage.duckdb import connect, create_parquet_views
from trs.storage.paths import default_duckdb_path, default_lock_path, project_root


def build_parser() -> argparse.ArgumentParser:
    root = project_root()
    parser = argparse.ArgumentParser(description="Run SQL against Vision Zero Copilot DuckDB Parquet views.")
    parser.add_argument("sql", help="SQL to execute, for example: \"show tables\"")
    parser.add_argument("--duckdb-path", default=str(default_duckdb_path(root)), help="DuckDB database path.")
    parser.add_argument("--lock-path", default=str(default_lock_path(root)), help="Generated manifest lock path.")
    parser.add_argument("--refresh-views", action="store_true", help="Recreate Parquet views before running SQL.")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    db_path = Path(args.duckdb_path).resolve()

    if args.refresh_views or not db_path.exists():
        lock = read_manifest_lock(Path(args.lock_path).resolve())
        create_parquet_views(db_path, lock["records"])

    with connect(db_path, read_only=True) as con:
        result = con.execute(args.sql)
        if result.description is None:
            return 0
        columns = [item[0] for item in result.description]
        rows = result.fetchall()

    print("\t".join(columns))
    for row in rows:
        print("\t".join("" if value is None else str(value) for value in row))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
