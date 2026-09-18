from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal


DecisionOutcome = Literal["matched", "clarification"]


@dataclass(frozen=True)
class IntentDecision:
    """Deterministic routing decision produced before the evidence engine runs."""

    outcome: DecisionOutcome
    template_id: str | None = None
    parameters: dict[str, Any] = field(default_factory=dict)
    location_text: str | None = None
    matched_rule: str | None = None
    candidates: tuple[str, ...] = ()
    message: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class CopilotResponse:
    """Application-layer response suitable for a UI, API, or evaluator."""

    status: str
    decision: IntentDecision
    summary: str
    packet: dict[str, Any] | None = None
    metrics: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "template_id": self.decision.template_id,
            "parameters": dict(self.decision.parameters),
            "location_text": self.decision.location_text,
            "decision": self.decision.to_dict(),
            "summary": self.summary,
            "packet": self.packet,
            "metrics": dict(self.metrics),
        }
