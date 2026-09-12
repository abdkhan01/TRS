from copy import deepcopy

import pytest

from trs.evidence.packet import build_evidence_packet, build_refusal_packet
from trs.evidence.schema import PacketValidationError, validate_packet


def test_build_evidence_packet_validates_contract() -> None:
    packet = build_evidence_packet(
        question="How many KSI collisions?",
        template_id="ksi_trend",
        status="answered",
        results={"ksi_collision_count": 3},
        source_ids=["ksi_collisions"],
        methods=["Count distinct ACCNUM."],
        caveat_ids=["ksi_party_grain"],
    )

    assert packet["status"] == "answered"
    assert packet["location"]["match_confidence"] == "unresolved"
    assert packet["sources"][0]["source_id"] == "ksi_collisions"
    assert packet["caveats"][0]["caveat_id"] == "ksi_party_grain"


def test_refusal_packet_uses_approved_reason() -> None:
    packet = build_refusal_packet(
        question="What should the City build?",
        template_id="recommendation",
        refusal_id="recommendation_not_supported",
    )

    assert packet["status"] == "refused"
    assert packet["results"] == {}
    assert packet["refusals"][0]["refusal_id"] == "recommendation_not_supported"


def test_schema_validation_reports_missing_required_field() -> None:
    packet = build_refusal_packet(
        question="What should the City build?",
        template_id="recommendation",
        refusal_id="recommendation_not_supported",
    )
    invalid = deepcopy(packet)
    del invalid["question"]

    with pytest.raises(PacketValidationError, match="packet.question is required"):
        validate_packet(invalid)
