# Phase 1 Hard Gaps Resolution Report

Last updated: 2026-08-22

## Purpose

This report analyzes the hard gaps identified in `docs/phase-1-resource-audit.md` and turns them into decision gates, resolution steps, and ownership recommendations for Phase 1 of Vision Zero Evidence Copilot.

The conclusion is a conditional go: engineering can continue on narrow deterministic scaffolding, evidence packets, resolver tests, and refusal behavior, but Phase 1 should not be treated as analyst-grade or pilot-ready until the spatial and counting gates are cleared.

## 2026-08-22 Engineering Resolution Status

The following gaps are now resolved by tracked engineering work:

- Toronto Centreline and the Intersection File have been downloaded into ignored local storage, refreshed from City open data, and profiled in `data_profiles/`.
- Traffic and Parking By-Law Schedules have been refreshed from the public datastore CSV and profiled as a candidate authority source.
- Traffic-volume raw CSV files now have reproducible row, key, and interval-date checks.
- `scripts/validate_data_profiles.py` validates local raw files against tracked profiles and checks registry/profile alignment.
- `datasets/` remains ignored; only metadata, caveats, and validation logic are tracked.

The remaining blockers are now mostly implementation gates:

- first resolver rules and confidence thresholds need implementation and analyst/geospatial review;
- severity/road-user field mappings still need analyst review before rich profile breakdowns are treated as official;
- posted speed-limit, CSZ, turn-restriction, and by-law-backed answers must remain refusal-only until the approved/candidate sources have implemented and tested lookup models.

## Decision Summary

Phase 1 is blocked by implementation work and remaining scope/governance boundaries:

1. Location resolution rules must be implemented, tested, and reviewed before intersection or corridor answers are enabled.
2. KSI and collision event-counting keys have Phase 1 approval, but severity and road-user mappings still need review for profile breakdowns.
3. Posted speed-limit and Community Safety Zone answers must remain refusal-only until source-specific lookup methods are implemented and tested.
4. The source registry and profiles must remain synchronized with refreshed raw data before evidence packets can be audited end to end.

Policy history, legal interpretation, intervention recommendations, causal safety-impact claims, ASE compliance claims, and bylaw-backed explanations should stay outside Phase 1 unless the project explicitly expands scope.

## Priority 1: Location Resolution

### Why This Is A Blocker

The core MVP questions depend on resolving user language such as "King St W and Spadina Ave", "this intersection", or "this corridor" into reviewed geometries. Without a trusted resolver, collision counts, KSI trends, ASE context, and traffic-volume context may be computed against the wrong point, segment, or buffer.

The current local workspace has refreshed Toronto Centreline and Intersection File copies in ignored raw storage, with tracked profiles and validation checks. The golden questions still depend on a reviewed resolver before answerable templates can move beyond refusal or manual fallback.

### Evidence Quality

High. The repository is internally consistent on this dependency, and Toronto Centreline is available as an official public dataset. Toronto Centreline provides linear features for streets and other mapped features, includes unique identifiers and names, and is published with GIS-friendly formats and daily refresh metadata.

Current local profile evidence:

- Toronto Centreline refreshed on 2026-08-21, with 64,341 rows and unique `_id` and `CENTRELINE_ID` values.
- Intersection File refreshed on 2026-08-20, with 46,270 rows and unique `_id` values.
- `INTERSECTION_ID` is not unique: 2,138 values duplicate across 2,142 extra rows, with sampled duplicates tied to multi-elevation pseudo-intersections.

### Resolution Steps

1. Done: Download Toronto Centreline and the Intersection File into ignored local raw storage.
2. Done: Profile both datasets using tracked `data_profiles/*.json` metadata.
3. Done: Record tracked metadata in `config/data_sources.yaml` and dedicated profile files.
4. Next: Choose a first resolver method:
   - intersections: normalized street-name pair lookup against the Intersection File;
   - corridors: named street plus cross-street bounds mapped to Centreline segments;
   - fallback: analyst-provided point or selected segment id.
5. Next: Emit match confidence, matched source ids, geometry type, buffer distance, and unresolved-candidate notes in every evidence packet.
6. Next: Validate the resolver against the current golden questions plus analyst-selected known intersections and corridors.

### MVP Gate

Do not enable normal intersection or corridor answers until:

- Centreline and Intersection File profiles validate against current local raw files;
- CRS and geometry handling are documented;
- a first resolver method is approved;
- at least 10 known location tests pass with reviewed match confidence;
- low-confidence matches produce refusal or review-needed output, not silent answers.

### Owner

Data engineer with Vision Zero analyst review. A geospatial analyst should review the resolver method if available.

## Priority 2: KSI And Collision Counting Governance

### Why This Is A Blocker

The KSI dataset appears to use involved-party rows, while many Phase 1 questions need collision-event counts. Counting rows when the analytical grain is collision events would inflate or distort KSI trends. The all-collision dataset also needs validation that one row equals one collision occurrence.

This is a public-sector trust issue. Counts can be caveated as draft during internal development, but the MVP should not present official-looking totals until the grain is approved.

### Evidence Quality

High. `docs/counting-methods.md`, `config/caveats.yaml`, and `config/data_sources.yaml` now record Phase 1 approval for `ACCNUM` KSI event counts and `_id` traffic-collision event counts while preserving grain caveats for involved-party breakdowns.

### Resolution Steps

1. Done: Validate and approve `ACCNUM` as the Phase 1 event-level identifier for KSI event counts.
2. Done: Validate and approve `_id` in the traffic-collisions dataset as one unique traffic collision occurrence for Phase 1.
3. Next: Define approved field mappings for:
   - fatal and serious injury status;
   - pedestrian, cyclist, motorist, passenger, motorcyclist, truck, transit, emergency, and other road-user groups;
   - date fields for event trends;
   - location fields used after spatial matching.
4. Create test cases comparing row counts vs unique-event counts for known KSI examples.
5. Add automated checks that fail when duplicate keys, missing event ids, missing dates, or unexpected severity values exceed documented thresholds.
6. Require an analyst review note before counts are considered MVP-approved.

### MVP Gate

Do not ship rich profile breakdowns as official until:

- severity and road-user field mappings are reviewed;
- count tests exist for at least one event-level total, one involved-party breakdown, and one trend;
- caveats distinguish event counts from involved-party breakdowns.

### Owner

Vision Zero analyst for approval, data engineer for validation and automated tests.

## Priority 3: Posted Speed Limits

### Why This Is A Scope Gate

The audit treats Area Speed Limit Reductions as useful context but not a complete current posted-speed-limit authority. That caution is correct. Observed speeds from the traffic-volume dataset are not legal posted speed limits, and the speed-limit-reduction program does not by itself prove current posted speed for every road segment.

External verification found an additional candidate source that changes the investigation path: Toronto has an open Traffic and Parking By-Law Schedules dataset for Municipal Code Chapter 950 schedules, including speed limits. This may be a better authoritative candidate than Area Speed Limit Reductions, but it needs schema review, schedule interpretation, spatial matching, and governance approval before factual speed-limit answers are enabled.

### Evidence Quality

Medium-high. The current repo evidence supports refusal-only behavior. The by-law schedules source appears promising and has now been downloaded from the public datastore CSV and profiled locally, but it has not been approved or mapped to road segments in this repo.

### Resolution Steps

1. Keep `posted_speed_limit_source_missing` refusal active until the Ontario Road Network speed-limit lookup is implemented and tested.
2. Done: Register Traffic and Parking By-Law Schedules as a candidate P1/P2 source in the source registry.
3. Partially done: Inspect whether the speed-limit schedule contains enough structured fields to map street segments, limits, sides/directions, temporal constraints, and amendment history.
4. Compare by-law speed-limit entries with Centreline segment names and limits.
5. Decide whether the MVP needs:
   - refusal-only posted speed answers;
   - limited by-law schedule lookup with strong caveats;
   - or full current speed-limit lookup after a proper spatial authority model is built.

### MVP Gate

The product owner must choose one of two states:

- Phase 1 refusal-only for posted speed limits until the ORN lookup is implemented; or
- Phase 1 includes ORN speed-limit ingestion, Toronto clipping, LRS matching, and sample validation.

No partial factual speed-limit answer should be allowed from observed speed data or area-reduction context alone.

Local profile note: the refreshed public by-law CSV has 27,592 rows. It includes 7 records in `Schedule 35: Speed Limits on Public Highways`, with `Highway`, `Between`, and `Speed Limit (km/h)` fields observed in the semi-structured `ByLaw_Table`. This is sufficient to justify continued investigation, not sufficient to enable posted-speed answers.

### Owner

Product owner for scope, policy/governance reviewer for authority, data engineer for profiling and matching.

## Priority 4: Community Safety Zone Status

### Why This Is A Scope Gate

The City's Community Safety Zone page provides useful policy context, but it is not a structured boundary or segment dataset. School proximity also does not prove legal CSZ status by itself. Therefore, factual "is this a CSZ?" answers should remain refusal-only until a structured authority source is available and approved.

External verification supports the current caution: the public CSZ page explains the designation concept and states that school frontages were designated, but it does not provide a direct structured segment inventory suitable for deterministic lookup.

### Evidence Quality

High for refusal-only behavior with current sources. Medium on whether a structured source is available through the Vision Zero Mapping Tool, internal GIS, or by-law schedules, because that still needs investigation.

### Resolution Steps

1. Keep `csz_structured_source_missing` refusal active.
2. Partially done: Investigate whether CSZ designations are available in:
   - Traffic and Parking By-Law Schedules;
   - Chapter 397 or Chapter 950 schedules;
   - Vision Zero Mapping Tool layers;
   - internal Transportation Services GIS.
3. If a structured source exists, profile segment names, limits, designation dates, active/inactive status, and legal authority.
4. Use school locations only as context, never as proof of CSZ status.

Local profile note: the refreshed Traffic and Parking By-Law Schedules CSV includes 1 record in `Schedule 33: Community Safety Zones` and 49 records in `Schedule 11: Safety Zones`. This does not establish complete CSZ coverage or approval for factual CSZ status answers.

### MVP Gate

Allow factual CSZ answers only after a structured segment or boundary source is approved and a spatial lookup method is tested. Otherwise, Phase 1 should provide policy context and refusal text only.

### Owner

Policy/governance reviewer, geospatial analyst, and data engineer.

## Priority 5: Reproducibility-Grade Source Manifest

### Why This Is A Blocker

`config/data_sources.yaml` plus `data_profiles/*.json` now form a reproducibility-grade starting point, but they must stay synchronized with ignored local raw files. For public-sector analytical use, every source used in an answer needs tracked metadata about version, download time, row count, schema, grain, date range, CRS, caveats, and approval status.

Raw datasets must remain local-only and ignored, so the manifest and audit docs become the durable record.

### Evidence Quality

Medium-high. This is inferred from the gap between the current registry and the evidence-packet requirements in `docs/evidence-model.md`.

### Resolution Steps

1. Done for current Phase 1 registered local sources: complete tracked profiles using `docs/data-audit-template.md` concepts.
2. Done or started in tracked profiles:
   - downloaded at;
   - source last refreshed;
   - file size;
   - row and column counts;
   - CRS and geometry type;
   - candidate keys and duplicate counts;
   - date range and primary date fields;
   - approved grain and counting method;
   - caveat/refusal ids;
   - analyst approval status.
3. Done: Add a lightweight validation command that checks local raw files against tracked profile metadata.
4. Keep `datasets/` ignored and never commit raw data.

### MVP Gate

Every source used in an answered evidence packet must have a tracked profile and approved usage notes. Sources without profiles may be registered but should not power factual answers.

### Owner

Data engineer and QA/evaluation owner.

## Deferred Gaps That Should Stay Deferred

These gaps should not block narrow Phase 1 if refusals are enforced:

| Gap | Phase 1 behavior |
|---|---|
| Council and staff report history | Refuse policy-history questions unless a source is manually provided in the evidence packet. |
| Municipal Code legal interpretation | Refuse legal interpretation. Candidate by-law schedules may support structured facts later, not legal advice. |
| Intervention inventory | Refuse intervention presence, implementation date, before/after, and effect claims. |
| ASE charges or violations | Refuse ticket volume, compliance, and enforcement-effect claims unless a structured source is approved. |
| No-right-turn-on-red status/history | Keep refusal active until by-law schedule fields are profiled and mapped. |
| Recommendations | Refuse intervention recommendations in MVP. |
| Causal claims | Refuse unless a later phase adds approved evaluation designs. |

## Recommended Data-Readiness Spike

Run one focused spike before declaring Phase 1 ready. Items marked done are resolved locally as of 2026-08-22:

1. Done: Download and profile Toronto Centreline.
2. Done: Download and profile the Intersection File.
3. Done: Validate and approve KSI event counts using `ACCNUM` and compare against row counts.
4. Done: Validate and approve traffic-collision `_id` uniqueness and row grain.
5. Done: Inspect Area Speed Limit Reductions schema; keep it as context-only rather than a complete posted-speed authority.
6. Done locally, pending policy/legal review: Inspect Traffic and Parking By-Law Schedules for speed limits, prohibited turns, and possible CSZ schedule fields.
7. Check whether the Vision Zero Mapping Tool exposes structured layers for CSZ, School Safety Zones, and interventions.

## Implementation Guidance

Keep the first architecture deliberately small:

- local ignored raw data in `datasets/`;
- tracked source registry and profile docs/config;
- Python profiling and validation scripts;
- deterministic geospatial matching before any LLM summarization;
- evidence packets as the only AI input;
- refusal-first handling for unsupported legal, policy, causal, and recommendation requests.

Architecture improvement completed in principle: use tracked `data_profiles/` files, one per registered source, while keeping `config/data_sources.yaml` readable. Raw files stay out of git, and profile metadata is reviewable in PRs. The next architecture improvement should be a small deterministic resolver module with fixture-based tests for at least 10 reviewed intersections/corridors.

## Implementation Status

Started on 2026-05-18 in branch `P1-hard-gaps-resolution-implementation`. Updated on 2026-08-22 after refreshing public source metadata and local ignored raw files.

| Gap | Implemented in repo | Remaining gate |
|---|---|---|
| Location resolution | Refreshed and profiled Toronto Centreline and Intersection File. Added evidence-packet fields for `geometry_type`, `source_ids`, `matched_source_ids`, `buffer_meters`, and unresolved-candidate notes. Added current registry next actions for resolver design. | Implement and approve resolver method; validate at least 10 known locations. |
| KSI and collision counting governance | Added tracked profiles for local KSI and traffic-collisions files. Local profile confirms KSI has 18,957 rows and 4,956 distinct `ACCNUM` values. Added validation command and updated counting-method notes. | Event-counting keys are approved for Phase 1; severity and road-user mappings still need review before rich official breakdowns. |
| Posted speed limits | Kept refusal path active. Refreshed and profiled Traffic and Parking By-Law Schedules as a candidate unapproved authority source; observed 7 Schedule 35 speed-limit records in the current CSV. | Product/governance decision: refusal-only Phase 1 or expanded by-law schedule ingestion, spatial matching, and review. |
| Community Safety Zone status | Kept refusal path active, added school-context-not-proof caveat, and profiled by-law schedule candidates: 1 Schedule 33 Community Safety Zone record and 49 Schedule 11 Safety Zone records. | Identify and approve a complete structured CSZ segment/boundary source before factual CSZ answers. |
| Reproducibility-grade source manifest | Added and refreshed `data_profiles/*.json`; linked profiles from `config/data_sources.yaml`; updated audit template; strengthened `scripts/validate_data_profiles.py` to check profile metadata and registry alignment. | Keep profiles refreshed as raw sources change; require approved usage notes before any source powers factual evidence packets. |

Human-owned actions are tracked in `docs/human-in-loop-gap-actions.md`.

## External Sources Checked

- Toronto Centreline, official CKAN dataset: https://ckan0.cf.opendata.inter.prod-toronto.ca/en/dataset/toronto-centreline-tcl
- Area Speed Limit Reductions, official Open Data page: https://open.toronto.ca/dataset/area-speed-limit-reductions/
- Community Safety Zones, City of Toronto Vision Zero page: https://www.toronto.ca/services-payments/streets-parking-transportation/road-safety/vision-zero/vision-zero-dashboard/community-safety-zones-vision-zero/
- Traffic and Parking By-Law Schedules, official CKAN dataset: https://ckan0.cf.opendata.inter.prod-toronto.ca/dataset/traffic-and-parking-by-law-schedules
- Toronto Municipal Code chapters: https://www.toronto.ca/legdocs/bylaws/lawmcode.htm
- Vision Zero Annual Report 2025: https://www.toronto.ca/wp-content/uploads/2026/04/95d9-VZAR2025Finala.pdf
