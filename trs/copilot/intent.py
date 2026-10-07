from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date
from typing import Callable, Iterable

from trs.copilot.models import IntentDecision


SUPPORTED_TEMPLATE_IDS = frozenset(
    {
        "ksi_trend",
        "collision_profile",
        "intersection_safety_snapshot",
        "corridor_safety_snapshot",
        "historical_ase_context",
        "speed_volume_context",
        "posted_speed_limit_lookup",
        "csz_status_lookup",
        "turn_restriction_policy_history",
        "causal_evaluation",
        "recommendation",
    }
)

LOCATION_REQUIRED_TEMPLATE_IDS = frozenset(
    {
        "intersection_safety_snapshot",
        "corridor_safety_snapshot",
        "historical_ase_context",
        "speed_volume_context",
    }
)

REFUSAL_TEMPLATE_IDS = frozenset(
    {
        "posted_speed_limit_lookup",
        "csz_status_lookup",
        "turn_restriction_policy_history",
        "causal_evaluation",
        "recommendation",
    }
)

_DEICTIC_LOCATION = re.compile(
    r"\b(?:this|that|the selected)\s+(?:intersection|corridor|road|location|area)\b",
    re.IGNORECASE,
)
_YEAR = r"(?:19|20)\d{2}"
_RANGE_PATTERNS = (
    re.compile(rf"\b(?:from\s+)?(?P<start>{_YEAR})\s+(?:to|through|until|-)\s+(?P<end>{_YEAR})\b", re.I),
    re.compile(rf"\bbetween\s+(?P<start>{_YEAR})\s+and\s+(?P<end>{_YEAR})\b", re.I),
)
_LAST_YEARS = re.compile(r"\b(?:in\s+)?(?:the\s+)?last\s+(?P<count>\d{1,2})\s+years?\b", re.I)
_SINCE_YEAR = re.compile(rf"\bsince\s+(?P<start>{_YEAR})\b", re.I)
_SINGLE_YEAR = re.compile(rf"\b(?:in|during|for)\s+(?P<year>{_YEAR})\b", re.I)
DEFAULT_SNAPSHOT_PERIOD = {"start_year": 2019, "end_year": 2023}
_BUFFER_PATTERNS = (
    re.compile(r"\bwithin\s+(?P<buffer>\d{1,4})\s*(?:m|metres?|meters?)\b", re.I),
    re.compile(r"\b(?P<buffer>\d{1,4})\s*(?:m|metres?|meters?)\s+buffer\b", re.I),
)

_LOCATION_PREFIX = re.compile(
    r"\b(?:at|near|around|for|on)\s+(?P<location>[^?.]+?)"
    r"(?=\s+(?:from|between|during|since|within\s+\d+|in\s+(?:the\s+)?last|over\s+(?:the\s+)?last)\b|[?.]|$)",
    re.IGNORECASE,
)
_INTERSECTION_NOUN = re.compile(
    r"\bintersection\s+(?:of\s+)?(?P<location>[^?.]+?)"
    r"(?=\s+(?:from|between|during|since|in\s+(?:the\s+)?last)\b|[?.]|$)",
    re.IGNORECASE,
)
_CORRIDOR_LOCATION = re.compile(
    r"\b(?:for|near|on)\s+(?P<location>[^?.]+?\s+from\s+"
    r"(?!(?:19|20)\d{2}\b)[^?.]+?\s+to\s+(?!(?:19|20)\d{2}\b)[^?.]+?)"
    r"(?=\s+(?:from|between|during|since|in\s+(?:the\s+)?last)\s+(?:19|20)\d{2}|[?.]|$)",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class IntentRule:
    rule_id: str
    template_id: str
    patterns: tuple[re.Pattern[str], ...]
    guardrail: bool = False

    def matches(self, question: str) -> bool:
        return all(pattern.search(question) for pattern in self.patterns)


def _patterns(*values: str) -> tuple[re.Pattern[str], ...]:
    return tuple(re.compile(value, re.IGNORECASE) for value in values)


DEFAULT_RULES: tuple[IntentRule, ...] = (
    IntentRule(
        "recommendation_guardrail",
        "recommendation",
        _patterns(
            r"\b(?:recommend|recommendation|what\s+(?:intervention|measure).+should|"
            r"what\s+should.+(?:implement|build|change))\b"
        ),
        guardrail=True,
    ),
    IntentRule(
        "causal_guardrail",
        "causal_evaluation",
        _patterns(
            r"\b(?:did|does|do|has|have|caused?|cause|effect|effective|reduce[ds]?)\b|"
            r"\b(?:what|the)\s+impact\s+(?:of|on)\b",
            r"\b(?:collision|crash|fatal|injur|ksi|safety|camera|ase|intervention)",
        ),
        guardrail=True,
    ),
    IntentRule(
        "turn_restriction_guardrail",
        "turn_restriction_policy_history",
        _patterns(r"\b(?:right|left)\s+turn|\bturn\s+(?:restriction|prohibit)|\bno\s+(?:right|left)\s+turn"),
        guardrail=True,
    ),
    IntentRule(
        "posted_speed_guardrail",
        "posted_speed_limit_lookup",
        _patterns(r"\bposted\s+speed\s+limit\b|\bwhat(?:'s|\s+is)\s+the\s+speed\s+limit\b"),
        guardrail=True,
    ),
    IntentRule(
        "csz_guardrail",
        "csz_status_lookup",
        _patterns(r"\bcommunity\s+safety\s+zone\b|\bcsz\b"),
        guardrail=True,
    ),
    IntentRule(
        "historical_ase_context",
        "historical_ase_context",
        _patterns(
            r"\b(?:historical|historic|former|previous|past|were\s+there)\b",
            r"\b(?:ase|speed\s+camera|automated\s+speed\s+enforcement)",
        ),
    ),
    IntentRule(
        "speed_volume_context",
        "speed_volume_context",
        _patterns(r"\btraffic\s+volume\b|\bobserved\s+speed\b|\b(?:85th|95th)\s+percentile\s+speed\b"),
    ),
    IntentRule(
        "intersection_snapshot",
        "intersection_safety_snapshot",
        _patterns(
            r"^(?!.*\bcorridor\b).*\bsafety\s+snapshot\b|"
            r"\bintersection\s+(?:safety\s+)?snapshot\b|\bsnapshot\b.+\bintersection\b"
        ),
    ),
    IntentRule(
        "corridor_snapshot",
        "corridor_safety_snapshot",
        _patterns(r"\bcorridor\s+(?:safety\s+)?snapshot\b|\bsafety\s+snapshot\b.+\bcorridor\b"),
    ),
    IntentRule(
        "collision_profile",
        "collision_profile",
        _patterns(
            r"\bcollision\s+profile\b|\b(?:collision|crash)(?:es)?\b.+"
            r"\b(?:road\s+user|weather|light|impact\s+type|profile|breakdown)\b"
        ),
    ),
    IntentRule(
        "ksi_trend",
        "ksi_trend",
        _patterns(
            r"\bksi\b|\bkilled\s+or\s+seriously\s+injured\b",
            r"\b(?:collision|crash|count|trend|how\s+many|number)",
        ),
    ),
)


def _clean_location(value: str) -> str | None:
    cleaned = value.strip(" ,.;:-")
    cleaned = re.sub(r"^(?:the\s+)?(?:intersection|corridor|road|location)\s+(?:of\s+)?", "", cleaned, flags=re.I)
    if not cleaned or cleaned.lower() in {"toronto", "citywide", "the city"}:
        return None
    return cleaned


def extract_location(question: str, *, location_hint: str | None = None) -> tuple[str | None, bool]:
    """Return a location phrase and whether unresolved deictic language was used."""

    if _DEICTIC_LOCATION.search(question):
        if location_hint and _clean_location(location_hint):
            return _clean_location(location_hint), False
        return None, True

    for pattern in (_CORRIDOR_LOCATION, _INTERSECTION_NOUN, _LOCATION_PREFIX):
        matches = list(pattern.finditer(question))
        for match in reversed(matches):
            candidate = _clean_location(match.group("location"))
            if candidate:
                return candidate, False
    if location_hint and _clean_location(location_hint):
        return _clean_location(location_hint), False
    return None, False


def extract_date_parameters(question: str, *, current_year: int) -> tuple[dict[str, int], str | None]:
    """Extract an inclusive year range and return a validation message when invalid."""

    for pattern in _RANGE_PATTERNS:
        match = pattern.search(question)
        if match:
            start_year = int(match.group("start"))
            end_year = int(match.group("end"))
            if start_year > end_year:
                return {}, "The start year must not be later than the end year."
            return {"start_year": start_year, "end_year": end_year}, None

    match = _LAST_YEARS.search(question)
    if match:
        count = int(match.group("count"))
        if count < 1 or count > 50:
            return {}, "The requested relative date range must be between 1 and 50 years."
        return {"start_year": current_year - count + 1, "end_year": current_year}, None

    match = _SINCE_YEAR.search(question)
    if match:
        start_year = int(match.group("start"))
        if start_year > current_year:
            return {}, "The start year cannot be in the future."
        return {"start_year": start_year, "end_year": current_year}, None

    match = _SINGLE_YEAR.search(question)
    if match:
        year = int(match.group("year"))
        return {"start_year": year, "end_year": year}, None

    return {}, None


def extract_buffer_parameter(question: str) -> tuple[dict[str, int], str | None]:
    """Extract an optional spatial buffer expressed in metres."""

    for pattern in _BUFFER_PATTERNS:
        match = pattern.search(question)
        if match:
            buffer_meters = int(match.group("buffer"))
            if buffer_meters < 1 or buffer_meters > 5000:
                return {}, "The spatial buffer must be between 1 and 5,000 metres."
            return {"buffer_meters": buffer_meters}, None
    return {}, None


class IntentMapper:
    """Allow-listed, deterministic natural-language template mapper."""

    def __init__(
        self,
        *,
        rules: Iterable[IntentRule] = DEFAULT_RULES,
        year_provider: Callable[[], int] | None = None,
    ) -> None:
        self.rules = tuple(rules)
        self.year_provider = year_provider or (lambda: date.today().year)
        invalid = {rule.template_id for rule in self.rules} - SUPPORTED_TEMPLATE_IDS
        if invalid:
            raise ValueError(f"Rules reference templates outside the allow-list: {sorted(invalid)}")

    def map(self, question: str, *, location_hint: str | None = None) -> IntentDecision:
        normalized = " ".join(question.split())
        if not normalized:
            return IntentDecision(
                outcome="clarification",
                message="Enter a road-safety evidence question.",
            )

        matches = [rule for rule in self.rules if rule.matches(normalized)]
        guardrail_matches = [rule for rule in matches if rule.guardrail]
        active = guardrail_matches or matches
        template_ids = tuple(dict.fromkeys(rule.template_id for rule in active))
        if not active:
            return IntentDecision(
                outcome="clarification",
                message=(
                    "I can route KSI trends, collision profiles, intersection or corridor snapshots, "
                    "traffic volume/observed-speed context, historical ASE context, and "
                    "approved refusal topics. Please restate the request using one of those scopes."
                ),
            )
        if len(template_ids) > 1:
            return IntentDecision(
                outcome="clarification",
                candidates=template_ids,
                message="The request matches more than one evidence template. Choose one analysis at a time.",
            )

        rule = active[0]
        parameters, date_error = extract_date_parameters(normalized, current_year=self.year_provider())
        buffer_parameter, buffer_error = extract_buffer_parameter(normalized)
        parameters.update(buffer_parameter)
        if rule.template_id in {"intersection_safety_snapshot", "corridor_safety_snapshot"}:
            parameters = {**DEFAULT_SNAPSHOT_PERIOD, **parameters}
        if date_error or buffer_error:
            return IntentDecision(
                outcome="clarification",
                template_id=rule.template_id,
                matched_rule=rule.rule_id,
                message=date_error or buffer_error,
            )

        location_text, unresolved_reference = extract_location(normalized, location_hint=location_hint)
        needs_location = rule.template_id in LOCATION_REQUIRED_TEMPLATE_IDS
        mentions_location_scope = bool(
            re.search(r"\b(?:at|near|around|intersection|corridor|location)\b", normalized, re.I)
        )
        if (
            unresolved_reference and rule.template_id not in REFUSAL_TEMPLATE_IDS
        ) or (needs_location and not location_text):
            return IntentDecision(
                outcome="clarification",
                template_id=rule.template_id,
                parameters=parameters,
                matched_rule=rule.rule_id,
                message="Specify an intersection or corridor, or select one in the analyst interface.",
            )

        if rule.template_id in {"ksi_trend", "collision_profile"} and not parameters:
            return IntentDecision(
                outcome="clarification",
                template_id=rule.template_id,
                location_text=location_text,
                matched_rule=rule.rule_id,
                message="Specify a year, an inclusive year range, or a relative period such as 'last 5 years'.",
            )

        if mentions_location_scope and rule.template_id in {"ksi_trend", "collision_profile"} and not location_text:
            return IntentDecision(
                outcome="clarification",
                template_id=rule.template_id,
                parameters=parameters,
                matched_rule=rule.rule_id,
                message="Specify the intersection or corridor for this location-scoped analysis.",
            )

        return IntentDecision(
            outcome="matched",
            template_id=rule.template_id,
            parameters=parameters,
            location_text=location_text,
            matched_rule=rule.rule_id,
        )
