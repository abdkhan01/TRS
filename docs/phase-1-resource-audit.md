# Phase 1 Resource Audit

Last updated: 2026-05-18

## Purpose

Phase 1 defines what the Vision Zero Evidence Copilot can and cannot prove before implementation begins. This audit records the resources needed for the first evidence model, separates hard dependencies from deferred sources, and gives analysts a concrete checklist for approving source use.

## Minimum Resource Set For Phase 1

| Priority | Resource | Status | Why it is needed | Source |
|---|---|---|---|---|
| P0 | Traffic collisions | Local file present | Base descriptive collision snapshots and modal collision profiles. | `datasets/traffic_collisions/` |
| P0 | KSI collisions | Local file present | Fatal and serious injury trends, vulnerable road user profiles, and high-severity evidence. | `datasets/motor_vehicle_collisions_ksi/` |
| P0 | Traffic volume and observed speed counts | Local file present | Exposure and speed context where coverage exists. | `datasets/traffic_volume/` |
| P0 | ASE camera locations | Local file present | Historical ASE location context only. | `datasets/automated_speed_enforcement_cameras/` |
| P0 | Toronto Centreline | Registered, not downloaded | Required for corridor matching, street segment context, road names, and spatial joins. | https://open.toronto.ca/dataset/toronto-centreline-tcl/ |
| P0 | Intersection file | Registered, not downloaded | Required for intersection safety snapshots and match-confidence scoring. | https://data.urbandatacentre.ca/catalogue/city-toronto-intersection-file-city-of-toronto |
| P0 | Source/version manifest | Added | Required to make every answer reproducible and auditable. | `config/data_sources.yaml` |
| P0 | Counting methods | Added | Required because row counts are not always collision-event counts. | `docs/counting-methods.md` |
| P0 | Evidence model | Added | Defines entities, claim levels, evidence types, and MVP boundaries. | `docs/evidence-model.md` |
| P0 | Caveat and refusal libraries | Added | Required to prevent unsupported factual, legal, causal, and recommendation claims. | `config/caveats.yaml`, `config/refusals.yaml` |
| P1 | Area speed limit reductions | Registered, not downloaded | Provides speed-limit reduction program context, but may not provide complete current posted speed limits. | https://open.toronto.ca/dataset/area-speed-limit-reductions/ |
| P1 | Community Safety Zone reference | Registered as reference source | Needed for CSZ context and refusal wording until structured boundaries are available. | https://www.toronto.ca/services-payments/streets-parking-transportation/road-safety/vision-zero/vision-zero-dashboard/community-safety-zones-vision-zero/ |
| P1 | School locations | Registered, not downloaded | Useful for school-frontage and CSZ context, not sufficient alone to determine legal CSZ status. | https://open.toronto.ca/dataset/school-locations-all-types/ |
| P1 | Road classification reference | Registered as reference source | Needed for corridor context and comparable-location grouping. | https://www.toronto.ca/services-payments/streets-parking-transportation/traffic-management/road-classification-system/ |
| P1 | Vision Zero reference material | Registered as reference source | Needed for approved terminology, safety emphasis areas, and policy context. | City Vision Zero pages and reports |
| P2 | Council/staff reports | Deferred | Needed for "why was this implemented?" policy history questions. | Toronto Council MMIS / legdocs |
| P2 | Municipal Code and bylaws | Deferred | Needed for bylaw-backed answers and restriction authority. | https://www.toronto.ca/legdocs/bylaws/lawmcode.htm |
| P2 | Intervention inventory | Deferred | Needed for before/after analysis and recommendation support. | Vision Zero Mapping Tool / internal sources |
| P2 | ASE charges or violations | Missing | Needed for enforcement/compliance claims. Do not infer from camera-location data. | No current reliable local source |
| P2 | No-right-turn-on-red restrictions | Missing | Needed for seed-document examples about turn restrictions. | To investigate |

## Hard Phase 1 Gaps

1. **Location resolution is not yet trustworthy.** Centreline and an intersection file must be registered and profiled before analyst-grade intersection or corridor queries are implemented.
2. **Posted speed-limit coverage is incomplete.** The area speed-limit reductions dataset is useful context, but it must not be treated as a complete current speed-limit authority until verified.
3. **Community Safety Zone status is not yet structured.** The City CSZ page provides policy context, but a structured segment/boundary source is still needed for factual "is this a CSZ?" answers.
4. **KSI counting rules need analyst approval.** The KSI file appears to contain involved-party rows; official collision counts should use unique collision-event identifiers after validation.
5. **Policy-history questions remain out of MVP.** Bylaw, council report, and intervention-history retrieval should be deferred until the evidence foundation is stable.

## Repo Artifacts Added For Phase 1

- `config/data_sources.yaml`
- `config/caveats.yaml`
- `config/refusals.yaml`
- `docs/data-audit-template.md`
- `docs/counting-methods.md`
- `docs/evidence-model.md`
- `docs/missing-data-backlog.md`
- `schemas/evidence_packet.schema.json`
- `eval/golden_questions.yaml`

## Next Work

1. Download or ingest Toronto Centreline and Intersection File into local raw storage after data handling rules are finalized.
2. Profile every local and newly added dataset for row counts, schema, grain, date ranges, coordinate system, and refresh assumptions.
3. Review KSI and traffic-collision counting methods with a Vision Zero analyst.
4. Decide whether speed-limit and CSZ factual answers are in MVP or must remain refusal-only until structured authority sources are available.
