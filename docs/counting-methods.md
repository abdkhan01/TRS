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
| Traffic collisions | Collision occurrence row. Local profile found 772,516 rows and 772,516 distinct `_id` values. | Count unique `_id`; for Phase 1, `_id` is approved as one unique traffic collision occurrence. | Approved for Phase 1 ingestion and deterministic counts |
| Motor vehicle collisions involving KSI | Involved-party row. Local profile found 18,957 rows and 4,956 distinct `ACCNUM` values. | Count unique `ACCNUM` for event-level KSI collisions; count rows only for involved-party breakdowns. | Approved for Phase 1 event counts and ingestion |
| Traffic volume summary | Latest count summary per location/count id. | Count observations by `latest_count_id`; do not infer continuous coverage. | Needs validation |
| Traffic volume raw files | Observation rows by count/time/bin. | Aggregate only within known count windows and method-specific fields. | Needs validation |
| ASE camera locations | Camera location row. Local profile found 198 rows and 198 distinct `_id`/`FID` values. | Count camera-location records only; never infer ticket volume or compliance. | Approved for Phase 1 historical location context |

## Local Validation Command

Run this command after local datasets are refreshed:

```bash
python3 scripts/validate_data_profiles.py
```

The command compares ignored local CSV files with tracked `data_profiles/*.json` metadata for row counts, file sizes, key uniqueness, and date ranges. A failing validation should block evidence-packet generation from that source until the profile is updated and reviewed.

## Default Snapshot Rules

- Use event-level counts for collision totals.
- Use involved-party rows only for party attributes such as injury role, age band, vehicle type, pedestrian action, cyclist action, or driver condition.
- Always include the date range used for the count.
- Always include the spatial method, such as point buffer, segment match, or corridor polygon.
- Always expose whether counts are filtered by KSI source, all-collision source, or both.
- Never compare KSI event counts and all-collision row counts without explaining the grain difference.

## Open Analyst Questions

1. Which injury/severity fields should be used for official pedestrian, cyclist, motorist, fatal, and serious injury summaries?
2. What default intersection buffer should be used for a first MVP: 30m, 50m, 100m, or analyst-selected?
3. What corridor method should be used first: named street between cross streets, selected Centreline segments, or buffered polyline?
