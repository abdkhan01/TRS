#!/usr/bin/env python3
"""Validate local raw data against tracked Phase 1 source profiles.

The profiles are JSON so this command stays dependency-free during the early
local-only phase. It intentionally checks only metadata that can be reproduced
from ignored raw files without uploading or committing those files.
"""

from __future__ import annotations

import csv
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PROFILE_DIR = ROOT / "data_profiles"
csv.field_size_limit(sys.maxsize)


def parse_date(value: str) -> str | None:
    value = (value or "").strip()
    if not value:
        return None

    if value.isdigit():
        if len(value) == 4:
            return f"{value}-01-01"
        if len(value) >= 12:
            try:
                return datetime.fromtimestamp(int(value) / 1000, tz=timezone.utc).date().isoformat()
            except (OSError, OverflowError, ValueError):
                return None

    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%m/%d/%Y", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(value[:19], fmt).date().isoformat()
        except ValueError:
            continue
    return None


def profile_csv(path: Path, profile: dict[str, Any], tracked_file: dict[str, Any]) -> dict[str, Any]:
    candidate_keys = list(dict.fromkeys(
        tracked_file.get("candidate_primary_keys")
        or profile.get("candidate_primary_keys", []) + profile.get("candidate_event_keys", [])
    ))
    date_fields = tracked_file.get("date_fields") or profile.get("date_fields", [])
    key_values = {key: Counter() for key in candidate_keys}
    missing_keys = Counter()
    date_ranges = {field: [None, None] for field in date_fields}
    missing_dates = Counter()

    row_count = 0
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        columns = reader.fieldnames or []
        for row in reader:
            row_count += 1
            for key in candidate_keys:
                if key not in row:
                    continue
                value = row.get(key, "").strip()
                if not value:
                    missing_keys[key] += 1
                else:
                    key_values[key][value] += 1

            for field in date_fields:
                if field not in row:
                    continue
                parsed = parse_date(row.get(field, ""))
                if parsed is None:
                    missing_dates[field] += 1
                    continue
                current_min, current_max = date_ranges[field]
                if current_min is None or parsed < current_min:
                    date_ranges[field][0] = parsed
                if current_max is None or parsed > current_max:
                    date_ranges[field][1] = parsed

    return {
        "file_size_bytes": path.stat().st_size,
        "row_count": row_count,
        "column_count": len(columns),
        "columns": columns,
        "keys": {
            key: {
                "missing": missing_keys[key],
                "distinct": len(values),
                "duplicate_values": sum(1 for count in values.values() if count > 1),
                "duplicate_rows": sum(count - 1 for count in values.values() if count > 1),
            }
            for key, values in key_values.items()
        },
        "date_ranges": {
            field: {
                "missing_or_unparsed": missing_dates[field],
                "min": values[0],
                "max": values[1],
            }
            for field, values in date_ranges.items()
        },
    }


def compare(expected: Any, actual: Any, label: str, errors: list[str]) -> None:
    if expected != actual:
        errors.append(f"{label}: expected {expected!r}, found {actual!r}")


def validate_profile(profile_path: Path) -> list[str]:
    profile = json.loads(profile_path.read_text(encoding="utf-8"))
    errors: list[str] = []
    local_files = profile.get("local_files", [])

    if profile.get("status") != "available_local":
        return errors

    for tracked_file in local_files:
        rel_path = tracked_file["path"]
        path = ROOT / rel_path
        if not path.exists():
            errors.append(f"{profile_path.name}: missing local file {rel_path}")
            continue
        if path.suffix.lower() != ".csv":
            continue

        actual = profile_csv(path, profile, tracked_file)
        prefix = f"{profile_path.name}:{rel_path}"
        if "file_size_bytes" in tracked_file:
            compare(tracked_file["file_size_bytes"], actual["file_size_bytes"], f"{prefix} file_size_bytes", errors)
        if "row_count" in tracked_file:
            compare(tracked_file["row_count"], actual["row_count"], f"{prefix} row_count", errors)
        if "column_count" in tracked_file:
            compare(tracked_file["column_count"], actual["column_count"], f"{prefix} column_count", errors)

        for key, expected in tracked_file.get("key_checks", {}).items():
            actual_key = actual["keys"].get(key)
            if actual_key is None:
                errors.append(f"{prefix} key {key}: field not found")
                continue
            for metric, expected_value in expected.items():
                compare(expected_value, actual_key.get(metric), f"{prefix} key {key} {metric}", errors)

        for field, expected in tracked_file.get("date_checks", {}).items():
            actual_date = actual["date_ranges"].get(field)
            if actual_date is None:
                errors.append(f"{prefix} date field {field}: field not found")
                continue
            for metric, expected_value in expected.items():
                compare(expected_value, actual_date.get(metric), f"{prefix} date {field} {metric}", errors)

    return errors


def main() -> int:
    profiles = sorted(PROFILE_DIR.glob("*.json"))
    if not profiles:
        print("No data profile JSON files found.")
        return 1

    all_errors: list[str] = []
    for profile_path in profiles:
        all_errors.extend(validate_profile(profile_path))

    if all_errors:
        print("Data profile validation failed:")
        for error in all_errors:
            print(f"- {error}")
        return 1

    print(f"Validated {len(profiles)} data profiles.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
