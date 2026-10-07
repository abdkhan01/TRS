from __future__ import annotations

from pathlib import Path

from trs.copilot.evaluation import GoldenQuestionEvaluator
from trs.copilot.models import CopilotResponse, IntentDecision
from trs.copilot.summary import DeterministicSummarizer, LocalLLMSummarizer


def evidence_packet() -> dict:
    return {
        "packet_id": "p1",
        "status": "answered",
        "template_id": "ksi_trend",
        "results": {"ksi_collision_count": 3, "series": [{"year": 2023, "ksi_collision_count": 3}]},
        "sources": [{"source_id": "ksi_collisions", "source_name": "KSI collisions"}],
        "caveats": [{"caveat_id": "ksi_party_grain", "text": "grain"}],
        "refusals": [],
    }


def test_deterministic_summary_uses_packet_fields() -> None:
    summary = DeterministicSummarizer().summarize(evidence_packet())

    assert "Ksi collision count: 3" in summary
    assert "1 time-series observations" in summary
    assert "KSI collisions" in summary
    assert "1 packet caveat" in summary


def test_local_llm_is_disabled_and_falls_back_on_failure() -> None:
    calls: list[str] = []

    def generator(prompt: str) -> str:
        calls.append(prompt)
        raise RuntimeError("local runtime unavailable")

    disabled = LocalLLMSummarizer(generator=generator)
    enabled = LocalLLMSummarizer(generator=generator, enabled=True)

    expected = DeterministicSummarizer().summarize(evidence_packet())
    assert disabled.summarize(evidence_packet()) == expected
    assert calls == []
    assert enabled.summarize(evidence_packet()) == expected
    assert len(calls) == 1
    assert "ksi_collision_count" in calls[0]


def test_full_evaluator_checks_packet_contract(tmp_path: Path) -> None:
    golden = tmp_path / "golden.yaml"
    golden.write_text(
        """
questions:
  - id: test-1
    question: Show KSI
    expected_template: ksi_trend
    expected_status: answered_after_location_sources_available
    required_sources: [ksi_collisions]
    required_caveats: [ksi_party_grain]
""",
        encoding="utf-8",
    )

    def runner(question: str) -> CopilotResponse:
        return CopilotResponse(
            status="answered",
            decision=IntentDecision(outcome="matched", template_id="ksi_trend"),
            summary="summary",
            packet=evidence_packet(),
        )

    report = GoldenQuestionEvaluator(runner=runner).evaluate(golden)

    assert report["passed"] == 1
    assert report["failed"] == 0
