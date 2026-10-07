from pathlib import Path

from trs.copilot.evaluation import GoldenQuestionEvaluator
from trs.copilot.intent import IntentMapper, extract_buffer_parameter, extract_date_parameters, extract_location


def test_golden_questions_map_to_allow_listed_templates() -> None:
    report = GoldenQuestionEvaluator(intent_mapper=IntentMapper(year_provider=lambda: 2025)).evaluate(
        Path(__file__).parents[1] / "eval" / "golden_questions.yaml"
    )

    assert report["failed"] == 0, report["cases"]
    assert report["passed"] == 20


def test_extracts_typed_explicit_and_relative_date_ranges() -> None:
    assert extract_date_parameters("from 2019 through 2023", current_year=2025) == (
        {"start_year": 2019, "end_year": 2023},
        None,
    )
    assert extract_date_parameters("in the last 5 years", current_year=2025) == (
        {"start_year": 2021, "end_year": 2025},
        None,
    )
    assert extract_date_parameters("since 2020", current_year=2025) == (
        {"start_year": 2020, "end_year": 2025},
        None,
    )
    values, error = extract_date_parameters("from 2024 to 2020", current_year=2025)
    assert values == {}
    assert "start year" in str(error)


def test_extracts_location_without_absorbing_date_phrase() -> None:
    location, unresolved = extract_location(
        "How many KSI collisions occurred at King St W and Spadina Ave in the last 5 years?"
    )

    assert location == "King St W and Spadina Ave"
    assert unresolved is False


def test_extracts_corridor_location_and_routes_template() -> None:
    question = (
        "Give me a corridor safety snapshot for King St W from Spadina Ave "
        "to Bathurst St from 2019 to 2023."
    )

    location, unresolved = extract_location(question)
    decision = IntentMapper().map(question)

    assert (location, unresolved) == ("King St W from Spadina Ave to Bathurst St", False)
    assert decision.template_id == "corridor_safety_snapshot"
    assert decision.parameters == {"start_year": 2019, "end_year": 2023}


def test_extracts_typed_buffer_without_absorbing_it_into_location() -> None:
    question = "Give me a safety snapshot at King St W and Spadina Ave within 50 metres"

    assert extract_buffer_parameter(question) == ({"buffer_meters": 50}, None)
    location, unresolved = extract_location(question)
    decision = IntentMapper().map(question)

    assert (location, unresolved) == ("King St W and Spadina Ave", False)
    assert decision.parameters == {
        "start_year": 2019,
        "end_year": 2023,
        "buffer_meters": 50,
    }


def test_deictic_location_uses_ui_hint_or_requests_clarification() -> None:
    mapper = IntentMapper(year_provider=lambda: 2025)

    missing = mapper.map("Show the collision profile near this intersection in 2023")
    resolved = mapper.map(
        "Show the collision profile near this intersection in 2023",
        location_hint="Bloor St W and Spadina Ave",
    )

    assert missing.outcome == "clarification"
    assert missing.template_id == "collision_profile"
    assert resolved.outcome == "matched"
    assert resolved.location_text == "Bloor St W and Spadina Ave"
    assert resolved.parameters == {"start_year": 2023, "end_year": 2023}


def test_ambiguous_supported_request_does_not_choose_a_template() -> None:
    decision = IntentMapper(year_provider=lambda: 2025).map(
        "Show a KSI collision trend and collision profile from 2020 to 2023"
    )

    assert decision.outcome == "clarification"
    assert set(decision.candidates) == {"ksi_trend", "collision_profile"}


def test_guardrail_preempts_descriptive_match() -> None:
    decision = IntentMapper(year_provider=lambda: 2025).map(
        "Did the speed camera reduce the KSI collision trend from 2020 to 2023?"
    )

    assert decision.outcome == "matched"
    assert decision.template_id == "causal_evaluation"


def test_missing_period_for_period_dependent_template_requests_clarification() -> None:
    decision = IntentMapper().map("Show the citywide KSI collision trend")

    assert decision.outcome == "clarification"
    assert decision.template_id == "ksi_trend"
    assert "year" in str(decision.message)


def test_snapshot_without_period_uses_reviewed_default_window() -> None:
    decision = IntentMapper().map(
        "Give me a safety snapshot for King St W and Spadina Ave"
    )

    assert decision.parameters == {"start_year": 2019, "end_year": 2023}
