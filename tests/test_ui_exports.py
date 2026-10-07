from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

import pytest

from trs.ui.exports import evidence_filename, to_json, to_markdown


def packet() -> dict:
    return {
        "packet_id": "packet/42",
        "created_at": datetime(2026, 5, 18, 12, 0, tzinfo=timezone.utc),
        "question": "How many KSI collisions?",
        "template_id": "ksi_trend",
        "status": "answered",
        "location": {
            "input": "Toronto citywide",
            "resolved_name": None,
            "match_confidence": "unresolved",
            "method": "Citywide query",
        },
        "parameters": {"end_year": 2023, "start_year": 2019},
        "results": {"ksi_collision_count": Decimal("12")},
        "sources": [
            {
                "source_id": "ksi_collisions",
                "source_name": "KSI collisions",
                "version": "2023",
                "status": "available",
                "date_range": "2006-2023",
                "source_url": "https://example.test/ksi",
                "local_path": Path("data/ksi.parquet"),
            }
        ],
        "methods": ["Count distinct collision identifiers."],
        "caveats": [{"caveat_id": "party_grain", "text": "Review party-grain data."}],
        "refusals": [],
        "query_metadata": {"runtime_ms": 12.5, "sql_template": "ksi_trend_v1"},
    }


def test_json_export_is_stable_and_serializes_supported_types() -> None:
    first = to_json(packet())
    second = to_json(packet())

    assert first == second
    assert first.endswith("\n")
    assert '"created_at": "2026-05-18T12:00:00+00:00"' in first
    assert '"ksi_collision_count": "12"' in first
    assert '"local_path": "data/ksi.parquet"' in first
    assert first.index('"created_at"') < first.index('"packet_id"')


def test_markdown_export_contains_review_and_reproduction_sections() -> None:
    report = to_markdown(packet())

    assert report.startswith("# Vision Zero Copilot evidence report\n")
    assert "**Status:** Answered" in report
    assert '"ksi_collision_count": "12"' in report
    assert "## Location and assumptions" in report
    assert "| KSI collisions | ksi_collisions | 2023 | available | 2006-2023 |" in report
    assert "- Count distinct collision identifiers." in report
    assert "- Review party-grain data." in report
    assert "- runtime_ms: 12.5" in report
    assert report.endswith("\n")


def test_markdown_export_surfaces_refusal_and_missing_sources() -> None:
    refused = packet()
    refused["status"] = "refused"
    refused["sources"] = []
    refused["refusals"] = [
        {
            "refusal_id": "missing_source",
            "reason": "A reviewed source is not available.",
            "allowed_alternative": "Review the registered collision trend.",
        }
    ]

    report = to_markdown(refused)

    assert "**Status:** Refused" in report
    assert "| None | Not provided |" in report
    assert "- A reviewed source is not available." in report


def test_evidence_filename_is_portable_and_validates_extension() -> None:
    assert evidence_filename(packet(), ".json") == "vision-zero-ksi_trend-packet-42.json"
    assert evidence_filename(packet(), "md") == "vision-zero-ksi_trend-packet-42.md"
    with pytest.raises(ValueError, match="json.*md"):
        evidence_filename(packet(), "csv")
