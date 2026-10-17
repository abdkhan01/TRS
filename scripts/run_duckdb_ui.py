#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from trs.storage.duckdb import connect
from trs.storage.paths import default_duckdb_path


def port_number(value: str) -> int:
    port = int(value)
    if not 1 <= port <= 65_535:
        raise argparse.ArgumentTypeError("port must be between 1 and 65535")
    return port


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run DuckDB's local web UI.")
    parser.add_argument(
        "--db",
        type=Path,
        default=default_duckdb_path(),
        help="DuckDB database path (default: data/trs.duckdb).",
    )
    parser.add_argument(
        "--port",
        type=port_number,
        default=4213,
        help="Local HTTP port (default: 4213).",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    db_path = args.db.expanduser().resolve()

    with connect(db_path) as con:
        con.execute("INSTALL ui")
        con.execute("LOAD ui")
        con.execute(f"SET ui_local_port = {args.port}")
        con.execute("CALL start_ui_server()")

        print(f"DuckDB UI: http://localhost:{args.port}")
        try:
            input("Press Enter to stop.\n")
        except (EOFError, KeyboardInterrupt):
            pass
        finally:
            con.execute("CALL stop_ui_server()")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
