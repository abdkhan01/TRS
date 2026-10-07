from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from trs.copilot import CopilotService, IntentMapper, JsonlAuditLogger, load_audit_metrics


def packet(
    *,
    template_id: str,
    status: str = "answered",
    refusals: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    return {
        "packet_id": "packet-1",
        "created_at": "2026-01-01T00:00:00+00:00",
        "question": "question",
        "template_id": template_id,
        "status": status,
        "location": {
            "input": "Toronto citywide",
            "resolved_name": None,
            "geometry": None,
            "match_confidence": "unresolved",
            "method": "fixture",
        },
        "parameters": {},
        "results": {"ksi_collision_count": 12},
        "sources": [{"source_id": "ksi_collisions", "source_name": "KSI", "status": "available_local"}],
        "methods": ["fixture method"],
        "caveats": [{"caveat_id": "descriptive_not_causal", "text": "Descriptive only."}],
        "refusals": refusals or [],
        "query_metadata": {"runtime_ms": 1.0},
    }


class FakeEngine:
    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    def run(self, template_id: str, **kwargs: Any) -> dict[str, Any]:
        self.calls.append({"template_id": template_id, **kwargs})
        if template_id == "recommendation":
            return packet(
                template_id=template_id,
                status="refused",
                refusals=[
                    {
                        "refusal_id": "recommendation_not_supported",
                        "reason": "Recommendations are not supported.",
                        "allowed_alternative": "Request descriptive evidence.",
                    }
                ],
            )
        return packet(template_id=template_id)


class FakeResolver:
    def __init__(self, confidence: str = "high") -> None:
        self.confidence = confidence
        self.calls: list[str] = []

    def resolve(self, text: str) -> dict[str, Any]:
        self.calls.append(text)
        return {
            "input": text,
            "resolved_name": "Bloor St W / Spadina Ave",
            "geometry": {"type": "Point", "coordinates": [-79.4, 43.66]},
            "match_confidence": self.confidence,
            "method": "fixture resolver",
        }


def test_service_maps_resolves_runs_and_summarizes() -> None:
    engine = FakeEngine()
    resolver = FakeResolver()
    service = CopilotService(
        engine,
        resolver=resolver,
        intent_mapper=IntentMapper(year_provider=lambda: 2025),
    )

    response = service.ask(
        "How many KSI collisions occurred at Bloor St W and Spadina Ave in the last 5 years?"
    )

    assert response.status == "answered"
    assert response.decision.template_id == "ksi_trend"
    assert response.decision.parameters == {"start_year": 2021, "end_year": 2025}
    assert resolver.calls == ["Bloor St W and Spadina Ave"]
    assert engine.calls[0]["location"]["match_confidence"] == "high"
    assert "Ksi trend returned answered evidence" in response.summary
    assert response.metrics["total_runtime_ms"] >= 0


def test_unresolved_location_returns_clarification_without_engine_call() -> None:
    engine = FakeEngine()
    service = CopilotService(
        engine,
        resolver=FakeResolver(confidence="low"),
        intent_mapper=IntentMapper(year_provider=lambda: 2025),
    )

    response = service.ask("Give me a safety snapshot for Bloor St W and Spadina Ave")

    assert response.status == "clarification"
    assert "sufficient confidence" in response.summary
    assert engine.calls == []


def test_medium_confidence_location_requires_analyst_clarification() -> None:
    engine = FakeEngine()
    service = CopilotService(
        engine,
        resolver=FakeResolver(confidence="medium"),
        intent_mapper=IntentMapper(year_provider=lambda: 2025),
    )

    response = service.ask("Give me a safety snapshot for Bloor St W and Spadina Ave")

    assert response.status == "clarification"
    assert engine.calls == []


def test_refusal_guardrail_does_not_require_location_resolution() -> None:
    engine = FakeEngine()
    resolver = FakeResolver(confidence="low")
    response = CopilotService(engine, resolver=resolver).ask(
        "What intervention should the City implement at Bloor St W and Spadina Ave?"
    )

    assert response.status == "refused"
    assert response.decision.template_id == "recommendation"
    assert resolver.calls == []
    assert "Recommendations are not supported" in response.summary


def test_answer_facade_accepts_explicit_template_and_typed_overrides(tmp_path: Path) -> None:
    engine = FakeEngine()
    log_path = tmp_path / "audit.jsonl"
    service = CopilotService(engine, resolver=FakeResolver(), log_path=log_path)

    result = service.answer(
        "Run the selected analysis",
        template_id="intersection_safety_snapshot",
        location_text="Bloor St W and Spadina Ave",
        start_year=2020,
        end_year=2023,
        buffer_meters=50,
    )

    assert result["status"] == "answered"
    assert result["decision"]["template_id"] == "intersection_safety_snapshot"
    assert engine.calls[0]["parameters"] == {
        "start_year": 2020,
        "end_year": 2023,
        "buffer_meters": 50,
    }
    assert log_path.exists()


def test_answer_facade_rejects_template_outside_allow_list() -> None:
    engine = FakeEngine()
    result = CopilotService(engine).answer("Run it", template_id="arbitrary_sql")

    assert result["status"] == "clarification"
    assert engine.calls == []


def test_db_path_constructor_and_answer_facade_run_approved_refusal(tmp_path: Path) -> None:
    result = CopilotService(db_path=tmp_path / "unused.duckdb").answer(
        "What is the posted speed limit on this corridor?"
    )

    assert result["status"] == "refused"
    assert result["template_id"] == "posted_speed_limit_lookup"
    assert result["packet"]["refusals"][0]["refusal_id"] == "posted_speed_limit_source_missing"
    assert not (tmp_path / "unused.duckdb").exists()


def test_engine_exception_fails_without_claiming_evidence() -> None:
    class BrokenEngine:
        def run(self, template_id: str, **kwargs: Any) -> dict[str, Any]:
            raise RuntimeError("database unavailable")

    response = CopilotService(BrokenEngine()).ask(
        "Show the citywide KSI collision trend from 2020 to 2023"
    )

    assert response.status == "error"
    assert response.packet is None
    assert "No factual result" in response.summary


def test_jsonl_audit_is_append_only_and_metrics_are_aggregated(tmp_path: Path) -> None:
    path = tmp_path / "audit" / "events.jsonl"
    logger = JsonlAuditLogger(path)
    service = CopilotService(FakeEngine(), audit_logger=logger)

    service.ask("Show the citywide KSI collision trend from 2020 to 2023")
    service.ask("What intervention should the City implement?")

    lines = path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2
    first_event = json.loads(lines[0])
    assert first_event["template_id"] == "ksi_trend"
    assert first_event["event_type"] == "query"
    assert first_event["sources"] == ["ksi_collisions"]
    assert first_event["caveats"] == ["descriptive_not_causal"]
    assert first_event["llm_used"] is False
    metrics = load_audit_metrics(path)
    assert metrics["event_count"] == 2
    assert metrics["status_counts"] == {"answered": 1, "refused": 1}
    assert metrics["event_type_counts"] == {"query": 2}
    assert metrics["average_runtime_ms"] is not None
    assert metrics["median_runtime_ms"] is not None


def test_audit_logger_can_omit_raw_question(tmp_path: Path) -> None:
    path = tmp_path / "audit.jsonl"
    service = CopilotService(FakeEngine(), audit_logger=JsonlAuditLogger(path, include_question=False))

    service.ask("Show the citywide KSI collision trend from 2020 to 2023")

    assert "question" not in json.loads(path.read_text(encoding="utf-8"))
