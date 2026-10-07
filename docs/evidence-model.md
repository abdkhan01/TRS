# Evidence Model

Last updated: 2026-10-06

## Purpose

The evidence model defines the vocabulary and boundaries for Phase 1. It separates descriptive evidence that the MVP may produce from policy, causal, legal, and recommendation claims that require later governance.

## Core Entities

| Entity | Definition | MVP status |
|---|---|---|
| `intersection` | A resolved street intersection point or polygon with match confidence. | Required |
| `corridor` | A street corridor represented by Centreline segments, cross-street bounds, or a buffered line. | Required |
| `collision_event` | One collision occurrence used for event-level counts. | Required |
| `involved_party` | One party/person/vehicle record involved in a collision. | Required for breakdowns |
| `road_user` | Pedestrian, cyclist, motorist, passenger, motorcyclist, truck, transit, emergency vehicle, or other role. | Required |
| `volume_observation` | Traffic volume observation or summary for exposure context. | Required where available |
| `speed_observation` | Observed speed summary or speed bucket, not a posted speed limit. | Required where available |
| `safety_measure` | Recorded intervention such as ASE, LPI, traffic calming, bikeway, or restriction. | Deferred except ASE locations |
| `policy_document` | A City, provincial, council, or bylaw source document. | Deferred except citations/refusals |
| `bylaw_reference` | Legal authority for a restriction or designation. | Deferred |

## Evidence Types

| Evidence type | Description | MVP status |
|---|---|---|
| `descriptive_count` | Counts of collisions, KSI events, or records using approved counting rules. | Allowed |
| `trend` | Counts grouped over time using approved date fields. | Allowed |
| `profile_breakdown` | Breakdowns by severity, road user, time, light, weather, road condition, or impact type. | Allowed |
| `spatial_context` | Evidence based on resolved point, segment, buffer, or corridor method. | Allowed with caveats |
| `exposure_context` | Traffic volume or observed speed context where source coverage exists. | Allowed with caveats |
| `historical_program_context` | Historical ASE camera-location presence or absence. | Allowed with caveats |
| `policy_reference` | Policy or bylaw text used as authority. | Deferred |
| `missing_source_refusal` | Explicit statement that the system cannot answer because a source is missing or unapproved. | Required |

## Claim Levels

| Claim level | Definition | MVP behavior |
|---|---|---|
| `factual` | Directly computed or retrieved from an approved source. | Allowed |
| `descriptive_summary` | Plain-language summary of computed evidence. | Allowed |
| `policy_context` | Explanation of policy intent or authority from retrieved documents. | Refuse unless approved source is present |
| `legal_interpretation` | Interpretation of bylaws, provincial acts, or legal authority. | Refuse |
| `causal_claim` | Claim that a factor caused a safety outcome. | Refuse |
| `recommendation` | Suggested intervention, prioritization, or operational decision. | Refuse in MVP |

## Evidence Packet Requirements

Every answered packet must include:

- Question or template input.
- Template id.
- Location input and resolved geometry.
- Match confidence.
- Parameters such as date range and buffer distance.
- Results grouped by evidence type.
- Source ids and source versions.
- Method notes.
- Caveat ids and rendered caveat text.
- Refusals, if any part of the question is unsupported.
- Query metadata sufficient for reproduction.

## AI Boundary

AI may:

- Map a user question to an approved template.
- Extract constrained parameters from natural language.
- Summarize only the evidence packet content.
- Explain why a question is refused.

AI must not:

- Generate counts.
- Invent speed limits, CSZ status, bylaw authority, or implementation dates.
- Make causal claims.
- Recommend interventions.
- Hide caveats or uncertainty.
