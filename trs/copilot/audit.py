from __future__ import annotations

import json
import threading
from statistics import median
from collections import Counter
from collections.abc import Mapping
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


class JsonlAuditLogger:
    """Append one JSON audit event per line without rewriting prior events."""

    def __init__(self, path: Path, *, include_question: bool = True) -> None:
        self.path = path
        self.include_question = include_question
        self._lock = threading.Lock()

    def append(self, event: Mapping[str, Any]) -> None:
        payload = dict(event)
        payload.setdefault("logged_at", datetime.now(UTC).isoformat())
        if not self.include_question:
            payload.pop("question", None)
        line = json.dumps(payload, sort_keys=True, default=str, separators=(",", ":")) + "\n"
        with self._lock:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with self.path.open("a", encoding="utf-8") as handle:
                handle.write(line)
                handle.flush()


def load_audit_metrics(path: Path) -> dict[str, Any]:
    """Aggregate operational metrics from an audit log, skipping corrupt lines."""

    statuses: Counter[str] = Counter()
    templates: Counter[str] = Counter()
    event_types: Counter[str] = Counter()
    runtimes: list[float] = []
    corrupt_lines = 0
    if not path.exists():
        return {
            "event_count": 0,
            "status_counts": {},
            "template_counts": {},
            "event_type_counts": {},
            "average_runtime_ms": None,
            "median_runtime_ms": None,
            "corrupt_lines": 0,
        }
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            try:
                event = json.loads(line)
            except (json.JSONDecodeError, TypeError):
                corrupt_lines += 1
                continue
            statuses[str(event.get("status", "unknown"))] += 1
            event_types[str(event.get("event_type", "query"))] += 1
            template_id = event.get("template_id")
            if template_id:
                templates[str(template_id)] += 1
            runtime_ms = (event.get("metrics") or {}).get("total_runtime_ms")
            if isinstance(runtime_ms, (int, float)):
                runtimes.append(float(runtime_ms))
    return {
        "event_count": sum(statuses.values()),
        "status_counts": dict(statuses),
        "template_counts": dict(templates),
        "event_type_counts": dict(event_types),
        "average_runtime_ms": sum(runtimes) / len(runtimes) if runtimes else None,
        "median_runtime_ms": median(runtimes) if runtimes else None,
        "corrupt_lines": corrupt_lines,
    }
