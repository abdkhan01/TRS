from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import yaml

from trs.copilot.intent import IntentMapper
from trs.copilot.models import CopilotResponse


@dataclass(frozen=True)
class EvaluationCase:
    question_id: str
    passed: bool
    expected_template: str | None
    actual_template: str | None
    expected_status: str | None
    actual_status: str | None
    failures: tuple[str, ...]


def load_golden_questions(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        payload = yaml.safe_load(handle) or {}
    questions = payload.get("questions", [])
    if not isinstance(questions, list):
        raise ValueError(f"{path}: 'questions' must be a list")
    return [dict(item) for item in questions]


def _packet_ids(packet: Mapping[str, Any], field: str, id_field: str) -> set[str]:
    values = packet.get(field) or []
    return {
        str(value[id_field])
        for value in values
        if isinstance(value, Mapping) and value.get(id_field) is not None
    }


class GoldenQuestionEvaluator:
    """Evaluate intent-only coverage or complete application responses."""

    def __init__(
        self,
        *,
        runner: Callable[[str], CopilotResponse] | None = None,
        intent_mapper: IntentMapper | None = None,
    ) -> None:
        if runner is None and intent_mapper is None:
            raise ValueError("Provide a response runner or an intent mapper")
        self.runner = runner
        self.intent_mapper = intent_mapper

    def evaluate(self, path: Path) -> dict[str, Any]:
        cases = [self._evaluate_case(item) for item in load_golden_questions(path)]
        passed = sum(case.passed for case in cases)
        return {
            "total": len(cases),
            "passed": passed,
            "failed": len(cases) - passed,
            "cases": [asdict(case) for case in cases],
        }

    def _evaluate_case(self, item: dict[str, Any]) -> EvaluationCase:
        question_id = str(item.get("id", "unknown"))
        question = str(item.get("question", ""))
        expected_template = item.get("expected_template")
        expected_status = item.get("expected_status")
        failures: list[str] = []

        if self.runner is None:
            assert self.intent_mapper is not None
            decision = self.intent_mapper.map(question)
            actual_template = decision.template_id
            actual_status = decision.outcome
            if actual_template != expected_template:
                failures.append(f"template: expected {expected_template}, got {actual_template}")
            return EvaluationCase(
                question_id=question_id,
                passed=not failures,
                expected_template=expected_template,
                actual_template=actual_template,
                expected_status=None,
                actual_status=actual_status,
                failures=tuple(failures),
            )

        response = self.runner(question)
        actual_template = response.decision.template_id
        actual_status = response.status
        if actual_template != expected_template:
            failures.append(f"template: expected {expected_template}, got {actual_template}")
        if expected_status == "answered_after_location_sources_available":
            if actual_status not in {"answered", "partially_answered"}:
                failures.append(f"status: expected answered evidence, got {actual_status}")
        elif expected_status and actual_status != expected_status:
            failures.append(f"status: expected {expected_status}, got {actual_status}")

        packet = response.packet or {}
        required_refusal = item.get("required_refusal")
        if required_refusal and required_refusal not in _packet_ids(packet, "refusals", "refusal_id"):
            failures.append(f"missing refusal: {required_refusal}")
        for source_id in item.get("required_sources") or []:
            if str(source_id) not in _packet_ids(packet, "sources", "source_id"):
                failures.append(f"missing source: {source_id}")
        for caveat_id in item.get("required_caveats") or []:
            if str(caveat_id) not in _packet_ids(packet, "caveats", "caveat_id"):
                failures.append(f"missing caveat: {caveat_id}")

        return EvaluationCase(
            question_id=question_id,
            passed=not failures,
            expected_template=expected_template,
            actual_template=actual_template,
            expected_status=expected_status,
            actual_status=actual_status,
            failures=tuple(failures),
        )
