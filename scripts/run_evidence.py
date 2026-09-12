#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from trs.evidence.engine import EvidenceEngine
from trs.storage.paths import default_duckdb_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run an approved evidence template.")
    parser.add_argument("template_id", help="Template id from config/templates.yaml")
    parser.add_argument("question", help="Original analyst question")
    parser.add_argument("--db", type=Path, default=default_duckdb_path())
    parser.add_argument("--start-year", type=int)
    parser.add_argument("--end-year", type=int)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    parameters = {
        key: value
        for key, value in {
            "start_year": args.start_year,
            "end_year": args.end_year,
        }.items()
        if value is not None
    }
    packet = EvidenceEngine(args.db).run(
        args.template_id,
        question=args.question,
        parameters=parameters,
    )
    print(json.dumps(packet, indent=2, default=str))
    return 1 if packet["status"] == "error" else 0


if __name__ == "__main__":
    raise SystemExit(main())
