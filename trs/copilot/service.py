from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from time import perf_counter
from typing import Any, Protocol
from uuid import uuid4

from trs.copilot.audit import JsonlAuditLogger
from trs.copilot.intent import (
    LOCATION_REQUIRED_TEMPLATE_IDS,
    REFUSAL_TEMPLATE_IDS,
    SUPPORTED_TEMPLATE_IDS,
    IntentMapper,
)
from trs.copilot.models import CopilotResponse, IntentDecision
from trs.copilot.summary import DeterministicSummarizer, PacketSummarizer


class EvidenceEnginePort(Protocol):
    def run(
        self,
        template_id: str,
        *,
        question: str,
        parameters: dict[str, Any] | None = None,
        location: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]: ...


class LocationResolverPort(Protocol):
    def resolve(self, text: str) -> dict[str, Any]: ...


_ACCEPTED_LOCATION_CONFIDENCE = frozenset({"manual_or_verified", "high", "medium"})


def _elapsed_ms(start: float) -> float:
    return round((perf_counter() - start) * 1000, 3)


def _validate_location(location: Any, *, input_text: str) -> dict[str, Any] | None:
    if not isinstance(location, Mapping):
        return None
    required = {"input", "match_confidence", "method"}
    if not required.issubset(location):
        return None
    if str(location.get("match_confidence")) not in _ACCEPTED_LOCATION_CONFIDENCE:
        return None
    result = dict(location)
    result.setdefault("input", input_text)
    result.setdefault("resolved_name", None)
    result.setdefault("geometry", None)
    return result


class CopilotService:
    """Coordinate deterministic mapping, resolution, evidence, summary, and audit."""

    def __init__(
        self,
        engine: EvidenceEnginePort | str | Path | None = None,
        *,
        db_path: str | Path | None = None,
        resolver: LocationResolverPort | None = None,
        intent_mapper: IntentMapper | None = None,
        summarizer: PacketSummarizer | None = None,
        audit_logger: JsonlAuditLogger | None = None,
        log_path: str | Path | None = None,
    ) -> None:
        if isinstance(engine, (str, Path)):
            if db_path is not None:
                raise ValueError("Provide db_path once")
            db_path = engine
            engine = None
        if engine is None:
            if db_path is None:
                raise ValueError("Provide an evidence engine or db_path")
            from trs.evidence.engine import EvidenceEngine

            engine = EvidenceEngine(Path(db_path))
        if audit_logger is not None and log_path is not None:
            raise ValueError("Provide audit_logger or log_path, not both")
        if audit_logger is None and log_path is not None:
            audit_logger = JsonlAuditLogger(Path(log_path))
        self.engine = engine
        self.resolver = resolver
        self.intent_mapper = intent_mapper or IntentMapper()
        self.summarizer = summarizer or DeterministicSummarizer()
        self.audit_logger = audit_logger

    def answer(
        self,
        question: str,
        *,
        template_id: str | None = None,
        location_text: str | None = None,
        start_year: int | None = None,
        end_year: int | None = None,
        buffer_meters: int | None = None,
    ) -> dict[str, Any]:
        """Compatibility facade for the analyst UI and integration layer.

        Explicit values override extracted values only after allow-list and type
        checks. The richer :meth:`ask` API remains available to typed callers.
        """

        response = self.ask(
            question,
            location_hint=location_text,
            template_id=template_id,
            parameter_overrides={
                key: value
                for key, value in {
                    "start_year": start_year,
                    "end_year": end_year,
                    "buffer_meters": buffer_meters,
                }.items()
                if value is not None
            },
        )
        return response.to_dict()

    def ask(
        self,
        question: str,
        *,
        location_hint: str | None = None,
        template_id: str | None = None,
        parameter_overrides: dict[str, Any] | None = None,
    ) -> CopilotResponse:
        request_id = str(uuid4())
        total_start = perf_counter()
        mapping_start = perf_counter()
        decision = self.intent_mapper.map(question, location_hint=location_hint)
        metrics: dict[str, Any] = {"mapping_runtime_ms": _elapsed_ms(mapping_start)}

        if template_id is not None:
            if template_id not in SUPPORTED_TEMPLATE_IDS:
                decision = IntentDecision(
                    outcome="clarification",
                    message="The selected analysis is not in the approved template allow-list.",
                )
            else:
                decision = IntentDecision(
                    outcome="matched",
                    template_id=template_id,
                    parameters=dict(decision.parameters),
                    location_text=location_hint or decision.location_text,
                    matched_rule="explicit_template_selection",
                )

        if parameter_overrides and decision.outcome == "matched":
            invalid_parameter = self._validate_parameter_overrides(parameter_overrides)
            if invalid_parameter:
                decision = IntentDecision(
                    outcome="clarification",
                    template_id=decision.template_id,
                    location_text=decision.location_text,
                    matched_rule=decision.matched_rule,
                    message=invalid_parameter,
                )
            else:
                values = dict(decision.parameters)
                values.update(parameter_overrides)
                if values.get("start_year") is not None and values.get("end_year") is not None:
                    if values["start_year"] > values["end_year"]:
                        decision = IntentDecision(
                            outcome="clarification",
                            template_id=decision.template_id,
                            location_text=decision.location_text,
                            matched_rule=decision.matched_rule,
                            message="The start year must not be later than the end year.",
                        )
                    else:
                        decision = IntentDecision(
                            outcome="matched",
                            template_id=decision.template_id,
                            parameters=values,
                            location_text=decision.location_text,
                            matched_rule=decision.matched_rule,
                        )
                else:
                    decision = IntentDecision(
                        outcome="matched",
                        template_id=decision.template_id,
                        parameters=values,
                        location_text=decision.location_text,
                        matched_rule=decision.matched_rule,
                    )

        if (
            decision.outcome == "matched"
            and decision.template_id in LOCATION_REQUIRED_TEMPLATE_IDS
            and not decision.location_text
        ):
            decision = IntentDecision(
                outcome="clarification",
                template_id=decision.template_id,
                parameters=decision.parameters,
                matched_rule=decision.matched_rule,
                message="Specify an intersection or corridor, or select one in the analyst interface.",
            )

        if decision.outcome == "clarification":
            metrics.update({"engine_runtime_ms": 0.0, "summary_runtime_ms": 0.0})
            response = CopilotResponse(
                status="clarification",
                decision=decision,
                summary=decision.message or "Clarify the requested evidence scope.",
                metrics=metrics,
            )
            return self._finish(request_id, question, response, total_start)

        location = None
        if decision.location_text and decision.template_id not in REFUSAL_TEMPLATE_IDS:
            if self.resolver is None:
                return self._clarify_location(request_id, question, decision, metrics, total_start)
            resolution_start = perf_counter()
            try:
                candidate = self.resolver.resolve(decision.location_text)
            except Exception:
                candidate = None
            metrics["location_runtime_ms"] = _elapsed_ms(resolution_start)
            location = _validate_location(candidate, input_text=decision.location_text)
            if location is None:
                return self._clarify_location(request_id, question, decision, metrics, total_start)

        engine_start = perf_counter()
        try:
            packet = self.engine.run(
                str(decision.template_id),
                question=question,
                parameters=decision.parameters,
                location=location,
            )
        except Exception:
            metrics["engine_runtime_ms"] = _elapsed_ms(engine_start)
            metrics["summary_runtime_ms"] = 0.0
            response = CopilotResponse(
                status="error",
                decision=decision,
                summary="The evidence service could not complete the request. No factual result was produced.",
                metrics=metrics,
            )
            return self._finish(request_id, question, response, total_start)
        metrics["engine_runtime_ms"] = _elapsed_ms(engine_start)

        if not isinstance(packet, dict) or not isinstance(packet.get("status"), str):
            metrics["summary_runtime_ms"] = 0.0
            response = CopilotResponse(
                status="error",
                decision=decision,
                summary="The evidence service returned an invalid packet. No factual result was produced.",
                metrics=metrics,
            )
            return self._finish(request_id, question, response, total_start)

        summary_start = perf_counter()
        try:
            summary = self.summarizer.summarize(packet)
        except Exception:
            summary = DeterministicSummarizer().summarize(packet)
        metrics["summary_runtime_ms"] = _elapsed_ms(summary_start)
        response = CopilotResponse(
            status=str(packet["status"]),
            decision=decision,
            summary=summary,
            packet=packet,
            metrics=metrics,
        )
        return self._finish(request_id, question, response, total_start)

    @staticmethod
    def _validate_parameter_overrides(values: Mapping[str, Any]) -> str | None:
        allowed = {"start_year", "end_year", "buffer_meters"}
        unknown = set(values) - allowed
        if unknown:
            return "Unsupported analysis parameter: " + ", ".join(sorted(unknown))
        for name, value in values.items():
            if not isinstance(value, int) or isinstance(value, bool):
                return f"{name} must be an integer."
        if "buffer_meters" in values and values["buffer_meters"] <= 0:
            return "buffer_meters must be greater than zero."
        return None

    def _clarify_location(
        self,
        request_id: str,
        question: str,
        decision: IntentDecision,
        metrics: dict[str, Any],
        total_start: float,
    ) -> CopilotResponse:
        metrics.update({"engine_runtime_ms": 0.0, "summary_runtime_ms": 0.0})
        clarified = IntentDecision(
            outcome="clarification",
            template_id=decision.template_id,
            parameters=decision.parameters,
            location_text=decision.location_text,
            matched_rule=decision.matched_rule,
            message="The location could not be resolved with sufficient confidence. Check or select the location.",
        )
        response = CopilotResponse(
            status="clarification",
            decision=clarified,
            summary=str(clarified.message),
            metrics=metrics,
        )
        return self._finish(request_id, question, response, total_start)

    def _finish(
        self,
        request_id: str,
        question: str,
        response: CopilotResponse,
        total_start: float,
    ) -> CopilotResponse:
        metrics = dict(response.metrics)
        metrics["total_runtime_ms"] = _elapsed_ms(total_start)
        final = CopilotResponse(
            status=response.status,
            decision=response.decision,
            summary=response.summary,
            packet=response.packet,
            metrics=metrics,
        )
        if self.audit_logger is not None:
            packet = final.packet or {}
            event = {
                "event_type": "query",
                "request_id": request_id,
                "question": question,
                "status": final.status,
                "template_id": final.decision.template_id,
                "decision": final.decision.to_dict(),
                "packet_id": packet.get("packet_id"),
                "parameters": packet.get("parameters", final.decision.parameters),
                "location": packet.get("location"),
                "sources": [source.get("source_id") for source in packet.get("sources", [])],
                "caveats": [caveat.get("caveat_id") for caveat in packet.get("caveats", [])],
                "refusals": [refusal.get("refusal_id") for refusal in packet.get("refusals", [])],
                "llm_used": False,
                "metrics": final.metrics,
            }
            try:
                self.audit_logger.append(event)
            except OSError:
                # Evidence delivery must not fail because local operational logging is unavailable.
                pass
        return final
