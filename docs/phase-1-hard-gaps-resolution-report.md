# Phase 1 Hard Gaps Resolution Report

Last updated: 2026-05-18

## Purpose

This report analyzes the hard gaps identified in `docs/phase-1-resource-audit.md` and turns them into decision gates, resolution steps, and ownership recommendations for Phase 1 of Vision Zero Evidence Copilot.

The conclusion is a conditional go: engineering can start on narrow deterministic scaffolding, source profiling, evidence packets, and refusal behavior, but Phase 1 should not be treated as analyst-grade or pilot-ready until the spatial and counting gates are cleared.

## Decision Summary

Phase 1 is blocked by two true implementation dependencies and two scope/governance decisions:

1. Location resolution must be trustworthy before intersection or corridor answers are enabled.
2. KSI and collision counting rules must be validated and approved before official-looking counts are produced.
3. Posted speed-limit and Community Safety Zone answers must remain refusal-only unless authoritative structured sources are approved.
4. The source registry must mature into a reproducibility-grade manifest before evidence packets can be audited end to end.

Policy history, legal interpretation, intervention recommendations, causal safety-impact claims, ASE compliance claims, and bylaw-backed explanations should stay outside Phase 1 unless the project explicitly expands scope.

## Priority 1: Location Resolution

### Why This Is A Blocker

The core MVP questions depend on resolving user language such as "King St W and Spadina Ave", "this intersection", or "this corridor" into reviewed geometries. Without a trusted resolver, collision counts, KSI trends, ASE context, and traffic-volume context may be computed against the wrong point, segment, or buffer.

The current audit correctly marks Toronto Centreline and the Intersection File as P0 resources that are registered but not downloaded. The golden questions also depend heavily on those sources before answerable templates can move beyond refusal or manual fallback.

### Evidence Quality

High. The repository is internally consistent on this dependency, and Toronto Centreline is available as an official public dataset. Toronto Centreline provides linear features for streets and other mapped features, includes unique identifiers and names, and is published with GIS-friendly formats and daily refresh metadata.

### Resolution Steps

1. Download Toronto Centreline and the Intersection File into ignored local raw storage.
2. Profile both datasets using `docs/data-audit-template.md`.
3. Record tracked metadata in `config/data_sources.yaml` or a dedicated tracked profile file.
4. Choose a first resolver method:
   - intersections: normalized street-name pair lookup against the Intersection File;
   - corridors: named street plus cross-street bounds mapped to Centreline segments;
   - fallback: analyst-provided point or selected segment id.
5. Emit match confidence, matched source ids, geometry type, buffer distance, and unresolved-candidate notes in every evidence packet.
6. Validate the resolver against the current golden questions plus analyst-selected known intersections and corridors.

### MVP Gate

Do not enable normal intersection or corridor answers until:

- Centreline and Intersection File are profiled;
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

High. `docs/counting-methods.md`, `config/caveats.yaml`, and `config/data_sources.yaml` all identify KSI grain and event-key approval as unresolved.

### Resolution Steps

1. Validate whether `ACCNUM` is the correct event-level identifier for KSI event counts.
2. Validate whether `_id` in the traffic-collisions dataset is unique and event-grain.
3. Define approved field mappings for:
   - fatal and serious injury status;
   - pedestrian, cyclist, motorist, passenger, motorcyclist, truck, transit, emergency, and other road-user groups;
   - date fields for event trends;
   - location fields used after spatial matching.
4. Create test cases comparing row counts vs unique-event counts for known KSI examples.
5. Add automated checks that fail when duplicate keys, missing event ids, missing dates, or unexpected severity values exceed documented thresholds.
6. Require an analyst review note before counts are considered MVP-approved.

### MVP Gate

Do not ship answered KSI totals or official-style collision counts until:

- KSI event-counting rule is approved;
- traffic-collision row grain is validated;
- count tests exist for at least one event-level total, one involved-party breakdown, and one trend;
- caveats distinguish event counts from involved-party breakdowns.

### Owner

Vision Zero analyst for approval, data engineer for validation and automated tests.

## Priority 3: Posted Speed Limits

### Why This Is A Scope Gate

The audit treats Area Speed Limit Reductions as useful context but not a complete current posted-speed-limit authority. That caution is correct. Observed speeds from the traffic-volume dataset are not legal posted speed limits, and the speed-limit-reduction program does not by itself prove current posted speed for every road segment.

External verification found an additional candidate source that changes the investigation path: Toronto has an open Traffic and Parking By-Law Schedules dataset for Municipal Code Chapter 950 schedules, including speed limits. This may be a better authoritative candidate than Area Speed Limit Reductions, but it needs schema review, schedule interpretation, spatial matching, and governance approval before factual speed-limit answers are enabled.

### Evidence Quality

Medium-high. The current repo evidence supports refusal-only behavior. The by-law schedules source appears promising, but it has not been downloaded, profiled, or mapped to road segments in this repo.

### Resolution Steps

1. Keep `posted_speed_limit_source_missing` refusal active for Phase 1 until a structured authority source is approved.
2. Register Traffic and Parking By-Law Schedules as a candidate P1/P2 source in the source registry.
3. Inspect whether the speed-limit schedule contains enough structured fields to map street segments, limits, sides/directions, temporal constraints, and amendment history.
4. Compare by-law speed-limit entries with Centreline segment names and limits.
5. Decide whether the MVP needs:
   - refusal-only posted speed answers;
   - limited by-law schedule lookup with strong caveats;
   - or full current speed-limit lookup after a proper spatial authority model is built.

### MVP Gate

The product owner must choose one of two states:

- Phase 1 refusal-only for posted speed limits; or
- Phase 1 expanded to include structured by-law schedule ingestion, spatial matching, and policy/legal review.

No partial factual speed-limit answer should be allowed from observed speed data or area-reduction context alone.

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
2. Investigate whether CSZ designations are available in:
   - Traffic and Parking By-Law Schedules;
   - Chapter 397 or Chapter 950 schedules;
   - Vision Zero Mapping Tool layers;
   - internal Transportation Services GIS.
3. If a structured source exists, profile segment names, limits, designation dates, active/inactive status, and legal authority.
4. Use school locations only as context, never as proof of CSZ status.

### MVP Gate

Allow factual CSZ answers only after a structured segment or boundary source is approved and a spatial lookup method is tested. Otherwise, Phase 1 should provide policy context and refusal text only.

### Owner

Policy/governance reviewer, geospatial analyst, and data engineer.

## Priority 5: Reproducibility-Grade Source Manifest

### Why This Is A Blocker

`config/data_sources.yaml` is a good start, but it is not yet enough to reproduce evidence packets. For public-sector analytical use, every source used in an answer needs tracked metadata about version, download time, row count, schema, grain, date range, CRS, caveats, and approval status.

Raw datasets must remain local-only and ignored, so the manifest and audit docs become the durable record.

### Evidence Quality

Medium-high. This is inferred from the gap between the current registry and the evidence-packet requirements in `docs/evidence-model.md`.

### Resolution Steps

1. For each `available_local` and newly downloaded source, complete a profile using `docs/data-audit-template.md`.
2. Add tracked metadata for:
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
3. Add a lightweight validation command that checks local raw files against tracked profile metadata.
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

Run one focused spike before declaring Phase 1 ready:

1. Download and profile Toronto Centreline.
2. Download and profile the Intersection File.
3. Validate KSI event counts using `ACCNUM` and compare against row counts.
4. Validate traffic-collision `_id` uniqueness and row grain.
5. Inspect Area Speed Limit Reductions schema.
6. Inspect Traffic and Parking By-Law Schedules for speed limits, prohibited turns, and possible CSZ schedule fields.
7. Check whether the Vision Zero Mapping Tool exposes structured layers for CSZ, School Safety Zones, and interventions.

## Implementation Guidance

Keep the first architecture deliberately small:

- local ignored raw data in `datasets/`;
- tracked source registry and profile docs/config;
- Python profiling scripts;
- deterministic geospatial matching before any LLM summarization;
- evidence packets as the only AI input;
- refusal-first handling for unsupported legal, policy, causal, and recommendation requests.

Architecture improvement to consider while doing this work: create a tracked `data_profiles/` folder with one YAML file per registered source. That keeps `config/data_sources.yaml` readable while still making source-level profiling auditable. Raw files stay out of git, but the metadata becomes reviewable in PRs.

## Implementation Status

Started on 2026-05-18 in branch `P1-hard-gaps-resolution-implementation`.

| Gap | Implemented in repo | Remaining gate |
|---|---|---|
| Location resolution | Added evidence-packet fields for `geometry_type`, `source_ids`, `matched_source_ids`, `buffer_meters`, and unresolved-candidate notes. Added source-registry next actions for Centreline and Intersection File. | Download/profile Centreline and Intersection File; approve resolver method; validate at least 10 known locations. |
| KSI and collision counting governance | Added tracked profiles for local KSI and traffic-collisions files. Local profile confirms KSI has 18,957 rows and 4,956 distinct `ACCNUM` values. Added validation command and updated counting-method notes. | Analyst approval of `ACCNUM`, severity mappings, road-user mappings, and traffic-collision business grain. |
| Posted speed limits | Kept refusal path active and registered Traffic and Parking By-Law Schedules as a candidate unapproved authority source. Added caveat/refusal for unapproved by-law schedule use. | Product/governance decision: refusal-only Phase 1 or expanded by-law schedule ingestion and review. |
| Community Safety Zone status | Kept refusal path active, added school-context-not-proof caveat, and included CSZ as a candidate use for by-law schedule investigation. | Identify and approve a structured CSZ segment/boundary source before factual CSZ answers. |
| Reproducibility-grade source manifest | Added `data_profiles/*.json` and `scripts/validate_data_profiles.py`; linked profiles from `config/data_sources.yaml`; updated audit template. | Complete profiles for Centreline, Intersection File, area speed-limit reductions, schools, and any by-law schedule source after download. |

Human-owned actions are tracked in `docs/human-in-loop-gap-actions.md`.

## External Sources Checked

- Toronto Centreline, official CKAN dataset: https://ckan0.cf.opendata.inter.prod-toronto.ca/en/dataset/toronto-centreline-tcl
- Area Speed Limit Reductions, official Open Data page: https://open.toronto.ca/dataset/area-speed-limit-reductions/
- Community Safety Zones, City of Toronto Vision Zero page: https://www.toronto.ca/services-payments/streets-parking-transportation/road-safety/vision-zero/vision-zero-dashboard/community-safety-zones-vision-zero/
- Traffic and Parking By-Law Schedules, official CKAN dataset: https://ckan0.cf.opendata.inter.prod-toronto.ca/dataset/traffic-and-parking-by-law-schedules
- Toronto Municipal Code chapters: https://www.toronto.ca/legdocs/bylaws/lawmcode.htm
- Vision Zero Annual Report 2025: https://www.toronto.ca/wp-content/uploads/2026/04/95d9-VZAR2025Finala.pdf
