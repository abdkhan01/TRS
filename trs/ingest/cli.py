from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

from trs.ingest.parquet_writer import read_manifest_lock, write_manifest_lock, write_source_file_to_parquet
from trs.ingest.registry import iter_source_files
from trs.storage.duckdb import connect, create_parquet_views, list_views
from trs.storage.paths import default_duckdb_path, default_lock_path, default_processed_dir, default_registry_path, project_root


def _source_counts(files) -> Counter[str]:
    counts: Counter[str] = Counter()
    for item in files:
        if item.ingestible:
            counts[item.source_id] += 1
    return counts


def ingest(args: argparse.Namespace) -> int:
    root = Path(args.root).resolve()
    registry_path = Path(args.registry).resolve()
    processed_dir = Path(args.processed_dir).resolve()
    lock_path = Path(args.lock_path).resolve()
    include_sources = set(args.source or []) or None

    files = iter_source_files(registry_path, root=root, include_sources=include_sources)
    counts = _source_counts(files)
    records = []
    skipped = []

    for source_file in files:
        if not source_file.exists:
            skipped.append(
                {
                    "source_id": source_file.source_id,
                    "input_path": str(source_file.path),
                    "reason": "registered local path does not exist",
                }
            )
            continue
        if not source_file.ingestible:
            skipped.append(
                {
                    "source_id": source_file.source_id,
                    "input_path": str(source_file.path),
                    "reason": source_file.skipped_reason,
                }
            )
            continue
        print(f"ingesting {source_file.source_id}: {source_file.path}", flush=True)
        file_records, file_skipped = write_source_file_to_parquet(
            source_file,
            processed_dir=processed_dir,
            source_file_count=counts[source_file.source_id],
            overwrite=not args.no_overwrite,
        )
        skipped.extend(file_skipped)
        for record in file_records:
            records.append(record)
            print(f"wrote {record['view_name']}: {record['row_count']} rows -> {record['output_path']}")

    write_manifest_lock(lock_path, records, skipped)
    print(f"wrote manifest lock: {lock_path}")
    return 0


def create_views(args: argparse.Namespace) -> int:
    lock = read_manifest_lock(Path(args.lock_path).resolve())
    created = create_parquet_views(Path(args.duckdb_path).resolve(), lock["records"])
    for view_name in created:
        print(f"created view: {view_name}")
    return 0


def verify(args: argparse.Namespace) -> int:
    db_path = Path(args.duckdb_path).resolve()
    views = list_views(db_path)
    print("views:")
    for view_name in views:
        print(f"  {view_name}")

    failures = []
    with connect(db_path, read_only=True) as con:
        for view_name in views:
            row_count = con.execute(f'select count(*) from "{view_name}"').fetchone()[0]
            print(f"{view_name}: {row_count} rows")
            if row_count == 0:
                failures.append(f"{view_name} has zero rows")
            if args.describe:
                columns = con.execute(f'describe "{view_name}"').fetchall()
                print(json.dumps({"view": view_name, "columns": columns}, default=str))

    if failures:
        for failure in failures:
            print(f"verify failure: {failure}")
        return 1
    return 0


def run_all(args: argparse.Namespace) -> int:
    result = ingest(args)
    if result:
        return result
    return create_views(args)


def build_parser() -> argparse.ArgumentParser:
    root = project_root()
    parser = argparse.ArgumentParser(description="Ingest registered local datasets into Parquet and DuckDB views.")
    parser.add_argument("--root", default=str(root), help="Project root. Defaults to this repository.")
    parser.add_argument("--registry", default=str(default_registry_path(root)), help="Path to data_sources.yaml.")
    parser.add_argument("--processed-dir", default=str(default_processed_dir(root)), help="Output directory for Parquet files.")
    parser.add_argument("--lock-path", default=str(default_lock_path(root)), help="Generated manifest lock path.")
    parser.add_argument("--duckdb-path", default=str(default_duckdb_path(root)), help="DuckDB database path for views.")

    subparsers = parser.add_subparsers(dest="command", required=True)

    ingest_parser = subparsers.add_parser("ingest", help="Convert registered local CSV files to Parquet.")
    ingest_parser.add_argument("--source", action="append", help="Limit ingestion to a source id. Can be repeated.")
    ingest_parser.add_argument("--no-overwrite", action="store_true", help="Fail if a Parquet output already exists.")
    ingest_parser.set_defaults(func=ingest)

    views_parser = subparsers.add_parser("create-views", help="Create DuckDB views over Parquet files.")
    views_parser.set_defaults(func=create_views)

    verify_parser = subparsers.add_parser("verify", help="Verify DuckDB views are queryable.")
    verify_parser.add_argument("--describe", action="store_true", help="Print view schemas as JSON rows.")
    verify_parser.set_defaults(func=verify)

    all_parser = subparsers.add_parser("all", help="Run ingest and create-views.")
    all_parser.add_argument("--source", action="append", help="Limit ingestion to a source id. Can be repeated.")
    all_parser.add_argument("--no-overwrite", action="store_true", help="Fail if a Parquet output already exists.")
    all_parser.set_defaults(func=run_all)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
