# Vision Zero Evidence Copilot - Project Feasibility Plan

Last updated: 2026-10-06

> Historical feasibility and scope-decision record. The MVP described here has been implemented as a local evidence product; use `docs/mvp-acceptance.md` for its current state.

## Co-founder Verdict

Decision: go forward, but pivot the first release.

The original direction, a broad "Vision Zero AI Copilot" that answers factual questions, explains policies, and suggests interventions, is directionally valuable but too broad for a first product. The viable first product is a **Vision Zero Evidence Copilot**: an internal analyst tool that assembles reproducible, cited evidence for Toronto intersections and corridors.

The MVP should not be an autonomous recommendation engine. It should help analysts get to defensible evidence faster: collision counts, KSI trends, vulnerable road user patterns, volume/speed context where available, and clearly sourced caveats. AI should help with intent mapping and evidence summaries, not with raw facts, legal interpretation, causal claims, or safety recommendations.

## Why This Is Worth Building

Toronto's Vision Zero program is explicitly data-driven and focused on reducing fatalities and serious injuries, especially for vulnerable road users. The City also publishes substantial transportation and collision datasets through open data. That creates a real opening for a product that makes analyst-grade evidence easier to assemble, audit, and reuse.

The project is worth pursuing if the team stays disciplined around one job:

> Reduce the time and risk involved in assembling transparent road-safety evidence for a specific location.

This is not just a "ChatGPT needs more data" problem. The real workflow problem is fragmented evidence: collision records, KSI records, volume counts, camera locations, policy text, bylaws, council reports, and location geometry live in different places and have different grains. A generic LLM cannot safely join, count, cite, or caveat those sources.

## Recommended Product Positioning

Use this positioning for the first release:

> Vision Zero Evidence Copilot helps Toronto road-safety analysts produce reproducible, cited safety snapshots for intersections and corridors using approved datasets and transparent methods.

Avoid this positioning for now:

> AI system that recommends safety interventions or explains why the City made a policy decision.

That broader positioning creates trust, legal, and data-quality risk before the evidence foundation exists.

## AI Fit Assessment

AI is a good fit for:

- Classifying a user question into approved templates.
- Translating natural language into constrained query parameters.
- Explaining an already-computed evidence packet in plain language.
- Drafting memo-style text from cited evidence.
- Helping users understand why the system cannot answer a question yet.

AI is not a good fit for:

- Collision counts or KSI aggregation.
- Geospatial joins and buffer logic.
- Current speed-limit facts without authoritative data.
- Community Safety Zone or bylaw determinations without source retrieval.
- Legal interpretation.
- Causal safety-impact claims.
- Open-ended intervention recommendations.

The core product should be SQL/geospatial computation first, LLM summary second.

## Current Local Assets

Observed local resources:

| Resource | Local status | Feasibility value |
|---|---|---|
| `TRS - Vision Zero AI Copilot.md` | Seed concept document | Strong basis for scope, users, and POC rationale |
| `AGENTS.md` | Working guide | Useful, but still needs project-plan links after these docs are adopted |
| `README.md` | Dataset source links | Useful start, not yet a full data catalog |
| Traffic collisions CSV/GeoJSON | 772,516 data rows, 2014-2025 | Strong base for descriptive collision snapshots |
| KSI collisions CSV/GeoJSON | 18,957 data rows, 2006-2023 | Strong base, but rows appear to be involved-party records; counts must use event-level identifiers |
| ASE camera locations CSV/GeoJSON | 198 data rows | Useful only as historical/location context after ASE repeal |
| Traffic volume files | Raw 2015-2019 and 2021-2022; summary rows with dates up to 2025 | Useful context, but coverage is uneven and must be caveated |
| `.codex/*.toml` | Role-specific agent profiles | Useful for project planning and future delegation |

## Major Missing Assets

The current repo is not enough to answer several questions in the seed document. These are the main gaps:

| Missing asset | Why it matters | MVP handling |
|---|---|---|
| Toronto Centreline / intersection resolver | Required for reliable "at this intersection" and corridor queries | Hard dependency for robust MVP; use constrained fallback only |
| Posted speed limits | Required for "what is the speed limit" and speed-policy context | Refuse until added |
| Speed-limit change history | Required for "why was speed limit reduced" | Defer |
| Community Safety Zone and School Safety Zone boundaries | Required for CSZ status | Refuse until added |
| Toronto bylaws and Municipal Code excerpts | Required for rule authority | Defer to policy RAG phase |
| Council reports and staff reports | Required for policy history and rationale | Defer to policy RAG phase |
| Intervention inventory | Required for before/after analysis and recommendations | Defer |
| ASE tickets/violations | Required for enforcement effect or compliance claims | Refuse until added |

## Directional Risks Found

### 1. ASE is no longer a live enforcement program

The concept document treats Automated Speed Enforcement as an active policy area. Current public sources now require more careful framing. Toronto's ASE page states that ASE penalty orders are no longer issued as of November 14, 2025 because of provincial legislation, and the same page records Bill 56 as repealing municipal automated speed enforcement camera use in Ontario.

Product implication: ASE should be historical context in the MVP, not a forward-looking deployment or enforcement module.

### 2. Some proposed questions are not answerable from current data

Questions like "Why was this road designated as a Community Safety Zone?" and "When was no-right-turn-on-red implemented here?" require bylaws, designation data, and council records. The current repo does not contain those sources.

Product implication: the MVP must have strong cannot-answer behavior.

### 3. KSI data can be miscounted

The KSI file appears to include involved-party rows. Counting rows could overstate collision events. Event-level counting needs a validated identifier such as `ACCNUM` and analyst-approved rules.

Product implication: data grain and counting rules are a launch blocker.

### 4. The seed scope drifts into recommendations

The document says the POC has two question categories, but then adds recommendations and report-building. That is understandable ideation, but it is too wide for MVP.

Product implication: evidence snapshots now; recommendations later after an approved countermeasure library and evaluation method exist.

## Issues Misidentified Or Understated

Misidentified:

- "ChatGPT cannot answer local questions" is true, but incomplete. The harder problem is evidence governance, data grain, geospatial matching, and source provenance.
- ASE locations do not prove CSZ boundaries, ticket activity, violation volume, or safety impact.
- A speed-limit question is not just a current speed-limit lookup if the user asks "why"; it becomes a policy-history and implementation-history task.

Understated:

- Location resolution is the biggest technical product risk.
- Analyst trust depends on visible methods and caveats, not only answer quality.
- Policy volatility can invalidate old assumptions quickly.
- Equity implications must be handled carefully if complaint volume, enforcement history, or public requests become prioritization inputs.

Not identified:

- Need for a formal evidence packet contract.
- Need for a caveat library approved by policy/research reviewers.
- Need for golden evaluation questions before building AI summaries.
- Need for source versioning and query audit logs.
- Need to separate descriptive evidence from causal evaluation.

## Pivot Options Considered

### Option A: Continue as broad AI copilot

Not recommended for MVP. It creates too much risk around unsupported recommendations, legal interpretation, and policy claims.

### Option B: Pivot to Vision Zero Evidence Copilot

Recommended. This preserves the most valuable part of the idea while reducing risk. It creates a strong foundation for later policy reasoning and recommendations.

### Option C: Pivot away from AI entirely to dashboards

Not recommended as the main direction. Dashboards are useful, but the core user need is ad hoc location-specific evidence assembly and memo support. A deterministic evidence engine with optional AI summaries is more differentiated than another static dashboard.

### Option D: Pivot to public citizen road-safety assistant

Not recommended now. Public-facing road-safety answers require stronger governance, accessibility, legal review, and messaging discipline.

## Feasibility Rating

| Dimension | Rating | Rationale |
|---|---|---|
| User value | High | Analysts plausibly spend time assembling repeated location evidence |
| Data availability | Medium | Core collision data exists; policy/location datasets are missing |
| Technical feasibility | High for MVP | Local Python, SQL, DuckDB/Parquet, and simple UI are enough |
| AI feasibility | Medium | Useful for summaries, risky for reasoning unless constrained |
| Governance risk | Medium-high | Public-sector output must be transparent and caveated |
| Delivery risk | Medium | Main blockers are location resolution, counting rules, and source registry |
| Strategic value | High | Builds a reusable evidence foundation for later AI features |

Overall: feasible if first release is constrained.

## MVP Definition

The MVP is viable when it can answer:

- "Give me a safety snapshot for this intersection."
- "Show KSI trends near this location over this period."
- "Summarize collision profile by severity, road user, time, light, weather, and impact type."
- "Show available traffic volume and speed context near this location."
- "Is there historical ASE camera-location context near this location?"
- "Can you answer whether this is a CSZ / current speed limit / bylaw-backed restriction?" with a correct refusal when sources are missing.

## Success Signals

- At least 80% of pilot factual answers accepted by analysts without data correction.
- 100% of outputs include source, date/version, method, and caveats.
- 0 unsupported legal, policy, causal, or recommendation claims in pilot evaluation.
- Median factual query response under 10 seconds on local data.
- Full evidence snapshot generated in under 10 minutes.
- At least 5 pilot users return weekly during a 4-week pilot.

## Stop Or Reassess Conditions

Pause or pivot if any of these happen:

- No analyst users can be recruited for validation.
- Authoritative location resolution cannot be built or acquired from open data.
- Analysts do not trust outputs even when methods are transparent.
- The team cannot enforce refusal behavior around missing policy/legal sources.
- The product is pushed toward public recommendations before internal evidence quality is proven.

## Source Notes

Official/context sources checked:

- [City of Toronto Vision Zero Plan Overview](https://www.toronto.ca/services-payments/streets-parking-transportation/road-safety/vision-zero/vision-zero-plan-overview/)
- [City of Toronto Automated Speed Enforcement](https://www.toronto.ca/services-payments/streets-parking-transportation/road-safety/vision-zero/safety-initiatives/automated-speed-enforcement/)
- [City of Toronto Community Safety Zones](https://www.toronto.ca/services-payments/streets-parking-transportation/road-safety/vision-zero/vision-zero-dashboard/community-safety-zones-vision-zero/)
- [City of Toronto Open Data introduction](https://open.toronto.ca/docs/staff-guidance/introduction-to-open-data/)
- [Toronto Open Data Q1 2026 update](https://open.toronto.ca/quarterly-update-q1-2026/)
- [Ontario Bill 56, Building a More Competitive Economy Act, 2025](https://www.ontario.ca/laws/statute/s25011)
