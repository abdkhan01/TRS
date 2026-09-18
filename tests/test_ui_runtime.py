import sys
from pathlib import Path
from types import ModuleType

import json

from trs.ui.runtime import answer_question, log_export_event
from trs.geo.resolver import LocationResolver


def test_runtime_calls_copilot_service_contract(monkeypatch, tmp_path: Path) -> None:
    calls: dict = {}

    class FakeCopilotService:
        def __init__(self, db_path, *, resolver, log_path):
            calls["init"] = {
                "db_path": db_path,
                "resolver": resolver,
                "log_path": log_path,
            }

        def answer(self, question, **kwargs):
            calls["answer"] = {"question": question, **kwargs}
            return {"status": "answered"}

    package = ModuleType("trs.copilot")
    package.__path__ = []
    service = ModuleType("trs.copilot.service")
    service.CopilotService = FakeCopilotService
    monkeypatch.setitem(sys.modules, "trs.copilot", package)
    monkeypatch.setitem(sys.modules, "trs.copilot.service", service)

    db_path = tmp_path / "trs.duckdb"
    log_path = tmp_path / "copilot.jsonl"
    result = answer_question(
        db_path,
        "Show the safety snapshot",
        template_id="intersection_safety_snapshot",
        location_text="Bloor Street West and Keele Street",
        start_year=2019,
        end_year=2023,
        buffer_meters=50,
        log_path=log_path,
    )

    assert result == {"status": "answered"}
    assert calls["init"] == {
        "db_path": db_path,
        "resolver": calls["init"]["resolver"],
        "log_path": log_path,
    }
    assert isinstance(calls["init"]["resolver"], LocationResolver)
    assert calls["answer"] == {
        "question": "Show the safety snapshot",
        "template_id": "intersection_safety_snapshot",
        "location_text": "Bloor Street West and Keele Street",
        "start_year": 2019,
        "end_year": 2023,
        "buffer_meters": 50,
    }


def test_export_action_is_appended_to_audit_log(tmp_path: Path) -> None:
    path = tmp_path / "audit" / "events.jsonl"
    log_export_event(
        path,
        {"status": "answered", "template_id": "ksi_trend", "packet_id": "packet-1"},
        "json",
    )

    event = json.loads(path.read_text(encoding="utf-8"))
    assert event["event_type"] == "export"
    assert event["export_format"] == "json"
    assert event["packet_id"] == "packet-1"
