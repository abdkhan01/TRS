from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from trs.storage.paths import default_evidence_schema_path


class PacketValidationError(ValueError):
    """Raised when an evidence packet violates its JSON schema contract."""

    def __init__(self, errors: list[str]):
        self.errors = errors
        super().__init__("Invalid evidence packet: " + "; ".join(errors))


def load_packet_schema(path: Path | None = None) -> dict[str, Any]:
    with (path or default_evidence_schema_path()).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _matches_type(value: Any, expected: str) -> bool:
    checks = {
        "null": value is None,
        "object": isinstance(value, dict),
        "array": isinstance(value, list),
        "string": isinstance(value, str),
        "number": isinstance(value, (int, float)) and not isinstance(value, bool),
        "integer": isinstance(value, int) and not isinstance(value, bool),
        "boolean": isinstance(value, bool),
    }
    return checks.get(expected, True)


def _validate(value: Any, schema: dict[str, Any], location: str) -> list[str]:
    errors: list[str] = []
    expected = schema.get("type")
    expected_types = [expected] if isinstance(expected, str) else expected
    if expected_types and not any(_matches_type(value, item) for item in expected_types):
        return [f"{location} must be {' or '.join(expected_types)}"]

    if "enum" in schema and value not in schema["enum"]:
        errors.append(f"{location} must be one of {schema['enum']}")

    if schema.get("format") == "date-time" and isinstance(value, str):
        try:
            datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            errors.append(f"{location} must be an ISO 8601 date-time")

    if isinstance(value, dict):
        required = schema.get("required", [])
        for key in required:
            if key not in value:
                errors.append(f"{location}.{key} is required")
        properties = schema.get("properties", {})
        if schema.get("additionalProperties") is False:
            for key in value.keys() - properties.keys():
                errors.append(f"{location}.{key} is not allowed")
        for key, child in properties.items():
            if key in value:
                errors.extend(_validate(value[key], child, f"{location}.{key}"))

    if isinstance(value, list) and isinstance(schema.get("items"), dict):
        for index, item in enumerate(value):
            errors.extend(_validate(item, schema["items"], f"{location}[{index}]"))
    return errors


def validate_packet(
    packet: dict[str, Any],
    *,
    schema_path: Path | None = None,
) -> dict[str, Any]:
    errors = _validate(packet, load_packet_schema(schema_path), "packet")
    if errors:
        raise PacketValidationError(errors)
    return packet
