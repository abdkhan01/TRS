# Counting Methods

Last updated: 2026-05-18

## Purpose

The Evidence Copilot must avoid counting rows when the analytical question requires counting collision events, involved parties, or observations. This document defines initial counting rules for analyst review.

## Canonical Grains

| Grain | Meaning | Typical identifier |
|---|---|---|
| `collision_event` | One collision occurrence. | Event id such as `ACCNUM`, or a validated event key. |
| `involved_party` | One person or vehicle party involved in a collision. | Row id plus event id. |
| `location_candidate` | A resolved point, intersection, or segment used for filtering. | Centreline/intersection id, or generated resolver id. |
| `corridor_segment` | A street segment or group of segments forming an analyst-defined corridor. | Centreline id or generated corridor id. |
| `volume_observation` | One count observation at a place and time. | Count id plus interval. |
| `speed_observation` | One observed speed summary or bucket. | Count id plus interval/bucket. |
| `policy_document` | A source document used for policy context. | Document URL or council item id. |
| `intervention_record` | One recorded safety intervention at a place and time. | Intervention id. |

## Initial Dataset Rules

| Dataset | Current row grain assumption | MVP counting rule | Approval status |
|---|---|---|---|
| Traffic collisions | Collision occurrence row. | Count rows by `_id` only after verifying `_id` is unique and one row equals one collision occurrence. | Needs validation |
| Motor vehicle collisions involving KSI | Involved-party row. | Count unique `ACCNUM` for event-level KSI collisions; count rows only for involved-party breakdowns. | Needs analyst approval |
| Traffic volume summary | Latest count summary per location/count id. | Count observations by `latest_count_id`; do not infer continuous coverage. | Needs validation |
| Traffic volume raw files | Observation rows by count/time/bin. | Aggregate only within known count windows and method-specific fields. | Needs validation |
| ASE camera locations | Camera location row. | Count camera-location records only; never infer ticket volume or compliance. | Needs validation |

## Default Snapshot Rules

- Use event-level counts for collision totals.
- Use involved-party rows only for party attributes such as injury role, age band, vehicle type, pedestrian action, cyclist action, or driver condition.
- Always include the date range used for the count.
- Always include the spatial method, such as point buffer, segment match, or corridor polygon.
- Always expose whether counts are filtered by KSI source, all-collision source, or both.
- Never compare KSI event counts and all-collision row counts without explaining the grain difference.

## Open Analyst Questions

1. Is `ACCNUM` approved as the event-level identifier for KSI counts?
2. Does the traffic-collisions file contain one row per collision occurrence for all years?
3. Which injury/severity fields should be used for official pedestrian, cyclist, motorist, fatal, and serious injury summaries?
4. What default intersection buffer should be used for a first MVP: 30m, 50m, 100m, or analyst-selected?
5. What corridor method should be used first: named street between cross streets, selected Centreline segments, or buffered polyline?
