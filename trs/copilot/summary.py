from __future__ import annotations

import json
from collections.abc import Callable, Mapping, Sequence
from typing import Any, Protocol


class PacketSummarizer(Protocol):
    def summarize(self, packet: Mapping[str, Any]) -> str: ...


def _humanize(name: str) -> str:
    return name.replace("_", " ").strip().capitalize()


def _scalar_lines(results: Mapping[str, Any]) -> list[str]:
    lines = []
    for key, value in results.items():
        if isinstance(value, (str, int, float, bool)) or value is None:
            lines.append(f"{_humanize(str(key))}: {value}.")
    return lines


class DeterministicSummarizer:
    """Render only fields already present in a validated evidence packet."""

    def summarize(self, packet: Mapping[str, Any]) -> str:
        status = str(packet.get("status", "error"))
        template_id = str(packet.get("template_id", "unknown"))
        if status == "refused":
            refusals = packet.get("refusals") or []
            if refusals and isinstance(refusals[0], Mapping):
                reason = str(refusals[0].get("reason", "This request is outside the approved evidence scope."))
                alternative = refusals[0].get("allowed_alternative")
                return f"{reason}" + (f" {alternative}" if alternative else "")
            return "This request is outside the approved evidence scope."
        if status == "error":
            return "The deterministic evidence query could not be completed. No factual result was produced."

        results = packet.get("results")
        result_map = results if isinstance(results, Mapping) else {}
        lines = [f"{_humanize(template_id)} returned {status} evidence."]
        lines.extend(_scalar_lines(result_map))

        series = result_map.get("series")
        if isinstance(series, Sequence) and not isinstance(series, (str, bytes)) and series:
            lines.append(f"The evidence packet contains {len(series)} time-series observations.")
        breakdowns = [
            key
            for key, value in result_map.items()
            if isinstance(value, (Mapping, Sequence)) and not isinstance(value, (str, bytes)) and key != "series"
        ]
        if breakdowns:
            lines.append("Included breakdowns: " + ", ".join(_humanize(str(key)).lower() for key in breakdowns) + ".")

        sources = packet.get("sources") or []
        if isinstance(sources, Sequence):
            source_names = [
                str(source.get("source_name", source.get("source_id", "unknown source")))
                for source in sources
                if isinstance(source, Mapping)
            ]
            if source_names:
                lines.append("Sources: " + "; ".join(source_names) + ".")
        caveats = packet.get("caveats") or []
        if isinstance(caveats, Sequence) and caveats:
            lines.append(f"Review the {len(caveats)} packet caveat(s) before reuse.")
        return " ".join(lines)


class LocalLLMSummarizer:
    """Optional packet-only local LLM boundary with deterministic fallback.

    The caller supplies a local generator to avoid a hard dependency on an LLM
    runtime. The adapter is disabled unless explicitly enabled and never prevents
    the deterministic fallback from being returned.
    """

    def __init__(
        self,
        *,
        generator: Callable[[str], str] | None = None,
        enabled: bool = False,
        fallback: PacketSummarizer | None = None,
    ) -> None:
        self.generator = generator
        self.enabled = enabled
        self.fallback = fallback or DeterministicSummarizer()

    def summarize(self, packet: Mapping[str, Any]) -> str:
        fallback_text = self.fallback.summarize(packet)
        if not self.enabled or self.generator is None:
            return fallback_text
        prompt = (
            "Summarize this evidence packet only. Do not add facts, causes, legal interpretations, "
            "or recommendations. Preserve refusal behavior and mention caveats.\n\n"
            + json.dumps(packet, sort_keys=True, default=str)
        )
        try:
            result = self.generator(prompt).strip()
        except Exception:
            return fallback_text
        return result or fallback_text
