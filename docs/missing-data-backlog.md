# Missing Data Backlog

Last updated: 2026-08-22

This backlog separates raw dataset availability from answer-readiness. A dataset can be downloaded and profiled locally while still blocked for MVP use because the source needs analyst approval, legal/policy interpretation, spatial matching, or stronger counting rules.

Local raw files were checked against `datasets/`, with tracked metadata in `config/data_sources.yaml` and `data_profiles/`. Raw dataset files remain local-only and must not be committed.

## Approval Status Labels

| Status | Meaning |
|---|---|
| `approved_for_mvp` | Source and Phase 1 counting/location use are approved for MVP implementation, subject to normal method caveats. |
| `approved_limited_mvp` | Source can power limited Phase 1 outputs, but specific breakdowns or coverage claims still need caveats. |
| `approved_context_only` | Source may be shown as descriptive context only and must not be used as authority for legal, policy, causal, or recommendation claims. |
| `approved_source_lookup_pending` | Source is approved as the candidate authority, but lookup/transformation logic must be implemented and tested before factual answers are enabled. |
| `refusal_only` | Source is present but should only support refusal/context behavior until interpretation and governance are approved. |
| `deferred_phase_2` | Source is present but not part of Phase 1 answer behavior. |

## Downloaded Local Datasets

| Dataset | Local folder or files present | Tracked profile | Approval status | Current readiness |
|---|---|---|---|---|
| Traffic Collisions | `datasets/traffic_collisions/` | `data_profiles/traffic_collisions.json` | `approved_for_mvp` | Available locally; `_id` is approved for Phase 1 event counts. |
| KSI Collisions | `datasets/motor_vehicle_collisions_ksi/` | `data_profiles/ksi_collisions.json` | `approved_limited_mvp` | Available locally; `ACCNUM` is approved for Phase 1 event counts, while row-level party breakdowns must keep grain caveats. |
| Traffic Volume | `datasets/traffic_volume/` | `data_profiles/traffic_volume.json` | `approved_limited_mvp` | Available locally; usable only with coverage and observed-speed caveats. |
| Automated Speed Enforcement Locations | `datasets/automated_speed_enforcement_cameras/` | `data_profiles/automated_speed_enforcement_locations.json` | `approved_context_only` | Available locally; supports historical camera-location context only. |
| Toronto Centreline TCL | `datasets/toronto_centreline/` | `data_profiles/toronto_centreline.json` | `approved_for_mvp` | Available locally; powers the implemented local corridor resolver, pending human method review. |
| Toronto Intersection File | `datasets/toronto_intersection_file/` | `data_profiles/toronto_intersection_file.json` | `approved_for_mvp` | Available locally; powers the implemented local intersection resolver, pending human method review. |
| Area Speed Limit Reductions | `datasets/area_speed_limit_reductions/` | `data_profiles/area_speed_limit_reductions.json` | `approved_context_only` | Available locally; not a complete current posted-speed-limit authority. |
| Ontario Road Network: Road Net Element | `datasets/ontario_road_network_road_net_element/` | `data_profiles/ontario_road_network_road_net_element.json` | `approved_source_lookup_pending` | Available locally and approved as the Phase 1 speed-limit source candidate; LRS join, Toronto clipping, and sample validation are still needed before factual answers. |
| School Locations - All Types | `datasets/school_locations_all_types/` | `data_profiles/school_locations_all_types.json` | `approved_context_only` | Available locally; school proximity is context, not proof of CSZ or SSZ legal designation. |
| School Safety Zone Watch Your Speed Locations | `datasets/school_safety_zone_watch_your_speed_locations/` | `data_profiles/school_safety_zone_watch_your_speed_locations.json` | `approved_context_only` | Available locally; partial sign-location proxy, not an authoritative SSZ boundary inventory. |
| Traffic And Parking By-Law Schedules | `datasets/traffic_and_parking_bylaw_schedules/` | `data_profiles/traffic_and_parking_bylaw_schedules.json` | `refusal_only` | Available locally as an unapproved candidate for speed limits, CSZ records, and turn restrictions. |
| Automated Speed Enforcement Charges | `datasets/automated_speed_enforcement_charges/` | `data_profiles/automated_speed_enforcement_charges.json` | `deferred_phase_2` | Available locally as monthly aggregate charges; descriptive ticket-volume use remains deferred to Phase 2. |

## Still Missing Or Not Downloaded

| Priority | Source gap | Needed for | Current MVP behavior | Candidate source |
|---|---|---|---|---|
| P1 | Road classification structured layer profile | Corridor comparison and context. | Candidate ArcGIS REST source is registered but not downloaded/profiled; use KSI `ROAD_CLASS` only where present until a structured layer is approved. | https://gis.toronto.ca/arcgis/rest/services/cot_geospatial/FeatureServer |
| P1 | Vision Zero safety measures inventory | Intervention context, implementation history, and before/after analysis. | Candidate ArcGIS REST layers are registered but not downloaded/profiled; refuse intervention-history and before/after claims. | https://gis.toronto.ca/arcgis/rest/services/cot_geospatial2/FeatureServer |
| P2 | Broader Municipal Code / bylaw legal text index | Bylaw-backed legal authority, restriction history, and legal interpretation. | Traffic and Parking By-Law Schedules are downloaded as structured candidate records, but the broader Municipal Code text/index is deferred; refuse legal authority questions. | https://www.toronto.ca/legdocs/bylaws/lawmcode.htm |
| P2 | Council and staff reports | "Why was this implemented?" policy history. | Refuse policy-history questions unless a manually provided source is in the evidence packet. | Toronto Council MMIS / legdocs |
| P2 | Individual ASE violations | Fine-grained enforcement compliance analysis. | Monthly aggregate ASE charges are downloaded; refuse individual-violation and enforcement-effect claims. | Unknown public source; may require internal access or a scoped data request. |

## Downloaded But Still Gated

| Priority | Gate | Local evidence now available | Remaining blocker | Current MVP behavior |
|---|---|---|---|---|
| P0 | Location resolution | Toronto Centreline and Intersection File are downloaded and profiled locally. | Approve resolver method, CRS handling, confidence scoring, duplicate/elevation handling, and at least 10 known test locations. | Refuse or require review for unresolved/low-confidence location matches. |
| P0 | KSI and collision counting rules | KSI and Traffic Collisions are downloaded and profiled locally. | Approve KSI event key, severity mappings, road-user mappings, and all-collision business grain. | Do not publish official KSI/collision counts until approved. |
| P1 | Complete current posted speed limits | Ontario Road Network Road Net Element, Traffic And Parking By-Law Schedules, and Area Speed Limit Reductions are downloaded locally as candidate/context sources. | Implement the ORN speed-limit LRS join, Toronto clipping, and validate sample locations. | Refuse current posted-speed-limit answers until the lookup is implemented and tested. |
| P1 | Structured Community Safety Zone status | Traffic And Parking By-Law Schedules, School Locations, and Watch Your Speed sign locations are downloaded locally. | Confirm whether bylaw schedule records are sufficient authority; approve filtering, status rules, and spatial matching. | Refuse factual "is this a CSZ?" answers; school proximity can be contextual only. |
| P1 | School Safety Zone legal designation | Watch Your Speed sign locations and School Locations are downloaded locally. | Identify/approve an authoritative SSZ segment or boundary inventory if legal designation answers are in scope. | Refuse legal SSZ designation answers. |
| P2 | ASE ticket-volume claims | ASE monthly aggregate charges workbook is downloaded locally. | Approve grain, site/date fields, and wording for limited descriptive claims. | Keep ticket-volume answers review-gated; refuse enforcement-effect claims. |
| P2 | No-right-turn-on-red restriction status | Traffic And Parking By-Law Schedules are downloaded locally as a candidate source. | Implement and approve no-right-turn-on-red filtering, status/history interpretation, and location matching. | Refuse restriction status/history answers. |

## Backlog Rules

- A missing source may still be registered in `config/data_sources.yaml` with `status: missing`, `status: deferred`, `status: candidate_api_not_downloaded`, or another non-local status.
- `available_local` means raw files exist locally and tracked metadata/profile files exist; it does not mean the source is approved for factual MVP answers.
- Unsupported questions must map to a refusal id in `config/refusals.yaml`.
- A source moves to `available_local` only after row count, schema, grain, date range, and limitations are documented.
- If a downloaded source is only a candidate or proxy, keep the relevant refusal active until the interpretation and matching rules are approved.
