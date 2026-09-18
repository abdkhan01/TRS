from __future__ import annotations

import json
import re
from collections.abc import Mapping, Sequence
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any


def _json_default(value: Any) -> Any:
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, (set, frozenset)):
        return sorted(value, key=str)
    raise TypeError(f"Object of type {type(value).__name__} is not JSON serializable")


def to_json(packet: Mapping[str, Any]) -> str:
    """Return a stable, copy-ready JSON representation of an evidence packet."""
    return json.dumps(
        packet,
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
        default=_json_default,
    ) + "\n"


def _escape(value: Any) -> str:
    text = "" if value is None else str(value)
    return text.replace("\\", "\\\\").replace("|", "\\|").replace("\n", " ")


def _display(value: Any) -> str:
    if value is None or value == "":
        return "Not provided"
    if isinstance(value, bool):
        return "Yes" if value else "No"
    return str(value)


def _bullet_items(items: Sequence[Any], *, preferred_key: str | None = None) -> list[str]:
    lines: list[str] = []
    for item in items:
        if isinstance(item, Mapping):
            value = item.get(preferred_key) if preferred_key else None
            if value is None:
                value = "; ".join(
                    f"{key}: {_display(item[key])}" for key in sorted(item)
                )
        else:
            value = item
        lines.append(f"- {_display(value)}")
    return lines or ["- None"]


def to_markdown(packet: Mapping[str, Any]) -> str:
    """Render a deterministic analyst-readable Markdown evidence report."""
    canonical = json.loads(to_json(packet))
    status = str(canonical.get("status", "unknown")).replace("_", " ").title()
    location = canonical.get("location") or {}
    parameters = canonical.get("parameters") or {}
    sources = canonical.get("sources") or []
    methods = canonical.get("methods") or []
    caveats = canonical.get("caveats") or []
    refusals = canonical.get("refusals") or []
    metadata = canonical.get("query_metadata") or {}

    lines = [
        "# Vision Zero Copilot evidence report",
        "",
        f"**Status:** {_escape(status)}  ",
        f"**Question:** {_escape(canonical.get('question'))}  ",
        f"**Template:** {_escape(canonical.get('template_id'))}  ",
        f"**Packet ID:** {_escape(canonical.get('packet_id'))}  ",
        f"**Created:** {_escape(canonical.get('created_at'))}",
        "",
        "## Evidence",
        "",
        "```json",
        json.dumps(canonical.get("results") or {}, ensure_ascii=False, indent=2, sort_keys=True),
        "```",
        "",
        "## Location and assumptions",
        "",
        f"- Input: {_display(location.get('input'))}",
        f"- Resolved location: {_display(location.get('resolved_name'))}",
        f"- Match confidence: {_display(location.get('match_confidence'))}",
        f"- Location method: {_display(location.get('method'))}",
    ]
    for key in sorted(parameters):
        lines.append(f"- {_escape(key)}: {_escape(_display(parameters[key]))}")

    lines.extend(
        [
            "",
            "## Sources and versions",
            "",
            "| Source | ID | Version | Status | Date range | URL |",
            "|---|---|---|---|---|---|",
        ]
    )
    if sources:
        for source in sources:
            lines.append(
                "| "
                + " | ".join(
                    _escape(_display(source.get(key)))
                    for key in (
                        "source_name",
                        "source_id",
                        "version",
                        "status",
                        "date_range",
                        "source_url",
                    )
                )
                + " |"
            )
    else:
        lines.append(
            "| None | Not provided | Not provided | Not provided | Not provided | "
            "Not provided |"
        )

    lines.extend(["", "## Methods", "", *_bullet_items(methods)])
    lines.extend(
        ["", "## Caveats", "", *_bullet_items(caveats, preferred_key="text")]
    )
    lines.extend(
        ["", "## Refusals", "", *_bullet_items(refusals, preferred_key="reason")]
    )
    lines.extend(["", "## Reproducibility", ""])
    if metadata:
        for key in sorted(metadata):
            lines.append(f"- {_escape(key)}: {_escape(_display(metadata[key]))}")
    else:
        lines.append("- No query metadata provided")
    return "\n".join(lines) + "\n"


def evidence_filename(packet: Mapping[str, Any], extension: str) -> str:
    """Build a portable filename from stable evidence-packet identifiers."""
    suffix = extension.lower().lstrip(".")
    if suffix not in {"json", "md"}:
        raise ValueError("Evidence export extension must be 'json' or 'md'")
    template = str(packet.get("template_id") or "evidence")
    packet_id = str(packet.get("packet_id") or "report")
    stem = re.sub(r"[^a-zA-Z0-9._-]+", "-", f"{template}-{packet_id}").strip("-.")
    return f"vision-zero-{stem or 'evidence-report'}.{suffix}"
