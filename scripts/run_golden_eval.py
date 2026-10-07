#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from trs.copilot import CopilotService, GoldenQuestionEvaluator, IntentMapper, JsonlAuditLogger
from trs.evidence.engine import EvidenceEngine
from trs.geo.resolver import LocationResolver
from trs.storage.paths import default_duckdb_path, project_root


def build_parser() -> argparse.ArgumentParser:
    root = project_root()
    parser = argparse.ArgumentParser(description="Evaluate the Vision Zero golden-question set.")
    parser.add_argument("--golden", type=Path, default=root / "eval" / "golden_questions.yaml")
    parser.add_argument("--db", type=Path, default=default_duckdb_path(root))
    parser.add_argument("--audit-log", type=Path, help="Optional append-only JSONL audit path.")
    parser.add_argument(
        "--intent-only",
        action="store_true",
        help="Validate allow-listed template mapping without running the evidence engine.",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if args.intent_only:
        evaluator = GoldenQuestionEvaluator(intent_mapper=IntentMapper())
    else:
        logger = JsonlAuditLogger(args.audit_log) if args.audit_log else None
        service = CopilotService(
            EvidenceEngine(args.db),
            resolver=LocationResolver(args.db),
            audit_logger=logger,
        )
        evaluator = GoldenQuestionEvaluator(runner=service.ask)
    report = evaluator.evaluate(args.golden)
    print(json.dumps(report, indent=2, default=str))
    return 0 if report["failed"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
