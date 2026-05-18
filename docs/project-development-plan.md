# Vision Zero Evidence Copilot - Project Development Plan

Last updated: 2026-05-16

## Goal

Prepare the project for development of an internal Vision Zero Evidence Copilot. The first release will produce reproducible, cited evidence snapshots for Toronto intersections and corridors using approved local datasets and deterministic computations.

This plan stops at the point where engineers can start implementation with clear scope, risks, milestones, and acceptance criteria.

## Working Assumptions

- First release is internal-only.
- No paid infrastructure or paid SaaS dependencies during MVP.
- Python and SQL are preferred.
- The deterministic evidence packet is the source of truth.
- AI is optional for MVP usefulness and cannot replace SQL/geospatial computation.
- Engineering kickoff happens after this plan, a project charter, and a backlog are accepted.
- Target team:
  - Product owner or PM
  - Technical lead
  - Data engineer
  - Geospatial/data analyst
  - Full-stack or app engineer
  - AI engineer part-time
  - QA/evaluation owner
  - Policy/governance reviewer
  - 2-5 pilot analysts

## Timeline Summary

Recommended timebox from engineering kickoff to internal pilot: 10-12 weeks.

| Phase | Duration | Outcome |
|---|---:|---|
| 0. Alignment | 1 week | Scope, owners, and decision gates locked |
| 1. Data audit and evidence model | 2 weeks | Data catalog, grains, counting rules, caveats |
| 2. Query and evidence product design | 2 weeks | Template catalog and evidence packet spec |
| 3. Architecture readiness | 1 week | Backlog, repo plan, and technical decisions ready |
| 4. MVP build | 4-5 weeks | Local working product |
| 5. Validation and pilot readiness | 2 weeks | Golden tests, pilot review, go/no-go |
| 6. Next release planning | 1 week after pilot | Prioritized roadmap from pilot evidence |

## Phase 0: Project Alignment

Duration: 1 week

Objective: lock the product boundary before engineering starts.

Deliverables:

- Project charter.
- MVP scope statement.
- Non-goals list.
- Success metrics.
- Decision log.
- Pilot user list.
- Initial risk register.
- Source register skeleton.

Decision gate G0:

- Stakeholders accept that MVP is an evidence product, not a recommendation product.
- Public-facing release is out of scope.
- Unsupported policy/legal/causal claims are explicitly banned.

## Phase 1: Data Audit And Evidence Model

Duration: 2 weeks

Objective: define what the data can and cannot prove.

Work:

- Inventory local datasets and source URLs.
- Record file names, row counts, schemas, sizes, date ranges, download dates, and refresh assumptions.
- Define canonical grains:
  - Collision event
  - Involved-party row
  - Location candidate
  - Corridor segment
  - Volume observation
  - Speed observation
  - Policy document
  - Intervention record
- Lock KSI counting rules with analysts.
- Identify fields used for vulnerable road users, severity, weather, light, time, and impact type.
- Define missing-source flags for speed limits, CSZ, bylaws, intervention inventory, council reports, and ASE tickets.

Deliverables:

- Data catalog.
- Source/version manifest.
- Counting-method specification.
- Caveat library v0.
- Missing data backlog.

Decision gate G1:

- KSI and traffic collision counting rules approved.
- Dataset limitations accepted by pilot reviewers.
- Missing data behavior approved.

## Phase 2: Query And Evidence Product Design

Duration: 2 weeks

Objective: define exactly what questions the MVP supports.

MVP templates:

1. Intersection safety snapshot.
2. Corridor safety snapshot.
3. KSI trend by location and period.
4. Collision profile by road user, severity, time, weather, light, and impact type.
5. Speed/volume context where available.
6. Historical ASE camera-location context with former-program caveat.
7. Cannot-answer response for missing speed limits, CSZ, bylaws, interventions, council reports, or ASE tickets.

Work:

- Write template inputs, outputs, and refusal criteria.
- Define default time periods.
- Define location match uncertainty output.
- Define intersection buffer and corridor method options for analyst approval.
- Define evidence packet schema.
- Define summary style and memo export requirements.
- Create a golden set of 20-30 representative questions.

Deliverables:

- Query template catalog.
- Evidence packet schema.
- Refusal policy.
- Output mockups.
- Golden question set.
- Analyst review checklist.

Decision gate G2:

- Every supported answer has deterministic method notes.
- Every answer has source/caveat fields.
- Every unsupported question has a designed refusal.

## Phase 3: Architecture And Engineering Readiness

Duration: 1 week

Objective: make engineering start clean.

Work:

- Initialize or confirm local git repository before development.
- Confirm feature branch naming convention.
- Decide minimal tech stack.
- Define repo structure.
- Define test strategy.
- Define local environment setup.
- Define data storage rules so large raw files are not accidentally committed.
- Create initial ticket backlog.

Recommended stack:

- Python for ingestion, analysis, API/app logic.
- DuckDB for local analytical SQL.
- Parquet/GeoParquet for normalized local data.
- GeoPandas/Shapely for geospatial preprocessing.
- Streamlit for first internal UI, unless API separation is required.
- Optional FastAPI later when multiple interfaces are needed.
- Optional local LLM through Ollama or a configurable adapter.

Deliverables:

- Architecture decision record.
- Engineering backlog.
- Local development setup plan.
- Testing plan.
- Data handling policy.

Decision gate G3:

- Technical lead confirms MVP can run locally with free/open-source tools.
- Deterministic packet can run without LLM.

## Phase 4: MVP Build

Duration: 4-5 weeks

Objective: build the internal pilot product.

Sprint 1: Data foundation

- Set up repo structure.
- Create data manifest format.
- Build ingestion pipeline from current CSV/GeoJSON sources to Parquet/DuckDB.
- Add schema validation.
- Add row count/date range reports.
- Add deterministic tests for ingest.

Sprint 2: Evidence engine

- Implement location resolver abstraction.
- Implement constrained fallback for known locations if Centreline is not ready.
- Implement approved query templates.
- Implement evidence packet builder.
- Add method metadata and source metadata to every packet.

Sprint 3: Analyst workflow

- Build internal UI.
- Display evidence, source metadata, caveats, and location match assumptions.
- Add copy/export flow.
- Add cannot-answer UI states.
- Add query logs and response-time capture.

Sprint 4: AI summary and evaluation

- Add constrained intent mapping to approved templates.
- Add summary generator that can only use evidence packet content.
- Add refusal tests.
- Run golden tests.
- Tune performance.
- Package pilot setup instructions.

Decision gate G4:

- Golden tests pass.
- 100% outputs include source/date/version/method/caveats.
- Unsupported recommendation/legal/causal prompts are refused.
- Pilot reviewers approve wording and caveats.

## Phase 5: Validation And Pilot Readiness

Duration: 2 weeks

Objective: make sure the product can be trusted by pilot users.

Validation work:

- Analyst review of golden outputs.
- Regression test run for deterministic templates.
- Hallucination/refusal test run for AI summaries.
- Manual spot checks for KSI counts and traffic collision counts.
- Response-time testing on a normal laptop.
- UX test with pilot analysts.

Pilot metrics:

- Factual answer acceptance rate.
- Missing-source refusal correctness.
- Unsupported claim count.
- Median response time.
- Time to generate a full evidence snapshot.
- Weekly returning pilot users.
- Analyst feedback themes.

Decision gate G5:

- At least 80% factual answer acceptance in pilot review.
- 100% citation/caveat coverage.
- 0 unsupported legal/policy/causal/recommendation claims.
- Median factual response under 10 seconds.
- Full snapshot under 10 minutes.

## Phase 6: Next Release Planning

Objective: decide whether to expand after pilot.

Likely next release:

- Toronto Centreline/intersection resolver.
- CSZ and School Safety Zone boundaries.
- Posted speed limits and speed-limit reduction history.
- Road classification.
- Intervention inventory.
- Policy/bylaw retrieval.
- Exportable briefing memo.
- Analyst feedback loop.

Later releases:

- Before/after statistical evaluation.
- Equity lens with approved methodology.
- Intervention suggestion engine using an approved countermeasure library.
- Public-facing product only after governance approval.

## Critical Path

1. Scope lock: evidence copilot only.
2. Data grain approval, especially KSI counting.
3. Source manifest and versioning.
4. Location resolver strategy.
5. Query template approval.
6. Evidence packet schema.
7. Citation and caveat enforcement.
8. Golden evaluation set.
9. Analyst pilot signoff.

Highest-risk item: location resolution. If the system cannot reliably map "intersection" and "corridor" inputs to geography, users will not trust the rest of the result.

## Role Ownership

| Role | Owns |
|---|---|
| Product owner / PM | Scope, milestones, decision gates, stakeholder alignment |
| Technical lead | Architecture, repo standards, engineering review |
| Data engineer | Ingestion, schema validation, source manifest |
| Geospatial/data analyst | Location methods, spatial assumptions, count validation |
| Full-stack/app engineer | UI, export, app workflow |
| AI engineer | Intent mapping, summary guardrails, refusal behavior |
| QA/evaluation owner | Golden tests, regression tests, pilot metrics |
| Policy/governance reviewer | Caveat wording, legal/policy claim boundaries |
| Pilot analysts | Acceptance review and workflow feedback |

## Risk Register

| Risk | Severity | Mitigation | Owner |
|---|---:|---|---|
| ASE policy changed after Bill 56 | High | Treat ASE as historical context only | PM + policy reviewer |
| KSI row double-counting | High | Event-level count rules and tests | Data analyst |
| Missing speed limits/CSZ/bylaws | High | Cannot-answer behavior and missing-source flags | PM |
| Weak location resolver | High | Start constrained; prioritize Centreline data | Geospatial analyst |
| False causal explanations | High | Ban causal language unless formal method exists | AI engineer + QA |
| Unsupported legal/policy claims | High | Policy caveat library and reviewer signoff | Policy reviewer |
| Traffic volume incompleteness | Medium | Show coverage and date gaps | Data engineer |
| Data refresh uncertainty | Medium | Version manifest and refresh-date display | Data steward |
| Local LLM quality/performance | Medium | Keep LLM optional; deterministic packet remains useful | AI engineer |
| Public-sector trust risk | High | Transparent methods, audit logs, citations, refusals | PM |
| Equity risk | Medium | Defer equity conclusions until method/data approved | PM + analyst |
| No paid tools slows setup | Medium | Local-first stack, defer managed services | Technical lead |

## Engineering Handoff Checklist

Product:

- MVP scope approved.
- Non-goals approved.
- User roles approved.
- Success metrics approved.
- Golden questions drafted.

Business analysis:

- Functional requirements approved.
- Non-functional requirements approved.
- Answer/refusal policy approved.
- Open decisions documented.

Data:

- Source manifest started.
- Dataset caveats documented.
- Missing-source backlog prioritized.
- KSI counting method approved.
- Sample test locations selected.

Engineering:

- Git repo initialized before code work.
- Feature branch convention documented.
- Architecture decision recorded.
- Dev environment plan written.
- Test strategy written.
- Data storage policy written.

Governance:

- Policy reviewer assigned.
- Pilot analysts identified.
- Caveat wording approved.
- Feedback and triage process defined.

## Initial Ticket Epics

1. Data catalog and source registry.
2. Local data ingestion pipeline.
3. Location resolver abstraction.
4. Deterministic query templates.
5. Evidence packet schema and builder.
6. Answer/refusal policy engine.
7. Analyst UI and export flow.
8. AI intent mapper and constrained summarizer.
9. Logging and pilot metrics.
10. Golden test suite.

## Source Notes

- [City of Toronto Vision Zero Plan Overview](https://www.toronto.ca/services-payments/streets-parking-transportation/road-safety/vision-zero/vision-zero-plan-overview/)
- [City of Toronto Automated Speed Enforcement](https://www.toronto.ca/services-payments/streets-parking-transportation/road-safety/vision-zero/safety-initiatives/automated-speed-enforcement/)
- [City of Toronto Community Safety Zones](https://www.toronto.ca/services-payments/streets-parking-transportation/road-safety/vision-zero/vision-zero-dashboard/community-safety-zones-vision-zero/)
- [Toronto Open Data Q1 2026 update](https://open.toronto.ca/quarterly-update-q1-2026/)
- [Ontario Bill 56, Building a More Competitive Economy Act, 2025](https://www.ontario.ca/laws/statute/s25011)
