# Vision Zero Evidence Copilot - Software Architecture

Last updated: 2026-10-06

> Architecture decision record. Where this early target design differs from code, the implemented `trs/` package and `README.md` are authoritative.

## Architecture Decision

Build a local-first, SQL-first evidence system with a constrained AI layer.

The first release should not be a complex multi-service platform. It should be a small local application that can:

1. Register and validate approved datasets.
2. Normalize large CSV/GeoJSON files into local analytical storage.
3. Run deterministic SQL/geospatial templates.
4. Build an evidence packet with citations, assumptions, and caveats.
5. Optionally summarize the evidence packet with an LLM.
6. Display/export the result for analyst review.

## Architectural Principles

- Deterministic evidence first, AI second.
- Every answer must be reproducible from data version, template, parameters, and method.
- Every output must show source, date/version, method, and caveats.
- Missing evidence must produce a refusal, not a guess.
- Keep MVP local and cheap.
- Avoid new services unless they remove real complexity.
- Build an evidence packet contract before building rich UI or advanced AI features.

## Recommended MVP Stack

| Layer | Recommendation | Reason |
|---|---|---|
| Language | Python | Matches user skillset and data ecosystem |
| Query engine | DuckDB | Fast local analytical SQL over large files |
| Storage format | Parquet / GeoParquet | Efficient local columnar storage |
| Geospatial processing | GeoPandas, Shapely, PyProj | Good enough for preprocessing and spatial joins |
| UI | Streamlit first | Fast internal analyst workflow with minimal frontend complexity |
| API | Defer FastAPI unless needed | Avoid service split until multiple clients exist |
| LLM | Optional local adapter, for example Ollama | No paid tools; summary layer must be replaceable |
| Tests | Pytest | Simple Python test standard |
| Metadata | YAML or JSON manifest | Human-readable source registry |

## High-Level Flow

```text
User question or template input
        |
        v
Intent mapper / template selector
        |
        v
Location resolver
        |
        v
Deterministic query template
        |
        v
Evidence packet builder
        |
        +--> Answer policy / refusal checks
        |
        +--> Analyst UI and export
        |
        +--> Optional LLM summary from packet only
```

## Component Architecture

```text
trs/
  config/
    data_sources.yaml
    caveats.yaml
    templates.yaml
  ingest/
    source_registry.py
    load_collisions.py
    load_ksi.py
    load_traffic_volume.py
    load_ase_locations.py
    validate.py
  storage/
    duckdb.py
    parquet_paths.py
  geo/
    resolver.py
    buffers.py
    corridor.py
  analysis/
    templates/
      intersection_snapshot.sql
      corridor_snapshot.sql
      ksi_trend.sql
      collision_profile.sql
      volume_context.sql
      ase_context.sql
    runner.py
  evidence/
    packet.py
    citations.py
    caveats.py
    refusal.py
  ai/
    intent_mapper.py
    summarizer.py
    prompts.py
  ui/
    app.py
    components/
  export/
    markdown.py
    json_export.py
  eval/
    golden_questions.yaml
    run_eval.py
  tests/
```

This is a target structure, not a requirement to create all files on day one.

## Data Architecture

### Source Zone

Raw files remain in `datasets/` or an equivalent local data directory. Large datasets should not be committed directly once development starts. Git LFS may be temporary, but a long-term local data storage convention is needed.

Current source groups:

- Traffic collisions.
- KSI collisions.
- Traffic volume.
- ASE camera locations.

Missing source groups to register explicitly:

- Speed limits.
- Speed-limit change history.
- Community Safety Zones.
- School Safety Zones.
- Road centreline / intersections.
- Road classification.
- Bylaws and Municipal Code text.
- Council and staff reports.
- Intervention inventory.
- ASE tickets/violations.

### Manifest

Every dataset must have a manifest entry:

```yaml
id: traffic_collisions
name: Traffic Collisions
source_url: https://...
local_path: datasets/traffic_collisions/4ad77de0-a9e0-4725-95d9-dbce6776d6cf.csv
format: csv
downloaded_at: 2026-05-16
refresh_date: unknown
grain: collision_occurrence
geometry: point_wgs84
primary_keys:
  - _id
date_fields:
  - OCC_YEAR
limitations:
  - Verify event grain before using for official counts.
caveat_ids:
  - source_currency_unknown
```

Missing datasets should also be represented:

```yaml
id: community_safety_zones
status: missing
required_for:
  - csz_status
  - ase_eligibility_context
refusal_message: Current CSZ status cannot be determined from registered sources.
```

## Analytical Storage

Recommended local layout:

```text
data/
  raw/              # optional local raw data mirror, ignored by git
  processed/
    collisions.parquet
    ksi.parquet
    traffic_volume.parquet
    ase_locations.parquet
  trs.duckdb
  manifest.lock.json
```

DuckDB can query Parquet directly. This keeps the MVP simple and avoids running a database server.

Use PostGIS later if:

- The Centreline/intersection resolver becomes complex.
- Spatial joins become too slow or too hard to maintain in local files.
- Multiple users need concurrent access.
- Deployment moves from local pilot to shared internal service.

## Evidence Packet Contract

The evidence packet is the core system boundary. UI, exports, and AI summaries should all consume this object.

Example shape:

```json
{
  "packet_id": "uuid",
  "created_at": "2026-05-16T00:00:00Z",
  "question": "Safety snapshot for X and Y",
  "template_id": "intersection_snapshot_v1",
  "status": "answered",
  "location": {
    "input": "Leona Dr and Sheppard Ave W",
    "resolved_name": "Leona Dr / Sheppard Ave W",
    "geometry": {
      "type": "Point",
      "crs": "EPSG:4326"
    },
    "match_confidence": "manual_or_verified",
    "method": "intersection point with 50m buffer"
  },
  "parameters": {
    "start_year": 2019,
    "end_year": 2023,
    "buffer_meters": 50
  },
  "results": {
    "ksi_unique_collision_count": 0,
    "collision_count": 0,
    "road_user_breakdown": [],
    "volume_context": [],
    "ase_context": []
  },
  "sources": [
    {
      "source_id": "ksi_collisions",
      "source_name": "Motor Vehicle Collisions involving KSI",
      "version": "local-manifest-version",
      "date_range": "2006-2023"
    }
  ],
  "methods": [
    "KSI counts use unique ACCNUM, not involved-party row count.",
    "Spatial filter uses 50m buffer around resolved point."
  ],
  "caveats": [
    "This is descriptive evidence, not a causal finding.",
    "Location matching uncertainty should be reviewed before official use."
  ],
  "refusals": [],
  "query_metadata": {
    "sql_template": "intersection_snapshot_v1",
    "runtime_ms": 850
  }
}
```

## Answer Policy

The answer policy runs after packet generation and before AI summary.

It must block:

- Current speed-limit answers without speed-limit source.
- CSZ or School Safety Zone status without designation/boundary source.
- Bylaw applicability without bylaw retrieval.
- ASE effect claims without ticket/violation data and approved evaluation method.
- Causal claims without formal before/after methodology.
- Legal interpretation.
- Open-ended recommendations.

Allowed answer pattern:

```text
I cannot determine [claim] from the currently registered sources.
Available evidence does show [descriptive facts].
To answer [claim], the system needs [missing sources].
```

## LLM Architecture

The LLM is not a data source.

Allowed LLM inputs:

- User question.
- Approved template descriptions.
- Evidence packet fields.
- Approved caveats.

Disallowed LLM inputs:

- Raw unrestricted data files.
- Unverified web snippets.
- Hidden policy assumptions.

LLM tasks:

- Intent mapping to approved templates.
- Clarifying question generation when location or dates are missing.
- Summary generation from evidence packet only.
- Memo draft from evidence packet only.

LLM guardrails:

- Use structured outputs where possible.
- Validate template id and parameters before execution.
- Refuse if intent is outside templates.
- Summary must cite packet facts.
- Deterministic packet must be usable if LLM fails.

## Location Resolution

MVP location resolution should be intentionally modest.

The implemented local resolver now materializes a canonical reference layer
from the official Toronto Centreline and Intersection File during DuckDB view
creation. `LINEAR_NAME_ID`, `INTERSECTION_ID`, and Centreline endpoint
relationships are the identity backbone. Deterministic street normalization
and aliases are search aids only; parsed text is never treated as a canonical
identifier. A named intersection must resolve to one unique official point.
Ambiguous, low-confidence, and unresolved matches stop before evidence SQL is
run and require analyst clarification or verified coordinates.

Collision, KSI, ASE, and traffic-count rows are still selected spatially from
their source coordinates. They are not permanently assigned an intersection
ID merely because they fall inside a buffer; doing so would create false
precision for midblock and approximately geocoded events.

Version 0:

- Support manually entered coordinates.
- Support known test intersections from the golden set.
- Support analyst-selected corridor endpoints where possible.
- Surface unresolved or low-confidence states.

Version 1:

- Add Toronto Centreline and intersection data.
- Resolve street names and cross-streets.
- Generate corridor geometries from centreline segments.
- Record match confidence and alternatives.

Required method metadata:

- Geometry source.
- CRS.
- Buffer distance.
- Corridor definition.
- Match confidence.
- Reviewer override, if any.

## Query Templates

MVP templates:

| Template | Inputs | Output |
|---|---|---|
| `intersection_snapshot_v1` | location, period, buffer | Collision and KSI summary near point |
| `corridor_snapshot_v1` | corridor geometry, period, buffer | Collision and KSI summary along corridor |
| `ksi_trend_v1` | location, period, interval | KSI trend by year/month |
| `collision_profile_v1` | location, period | Breakdown by severity, user, time, weather, light, impact |
| `volume_context_v1` | location/corridor | Available volume/speed context and coverage gaps |
| `ase_context_v1` | location/corridor | Historical ASE camera proximity and former-program caveat |
| `cannot_answer_v1` | unsupported intent | Missing source explanation |

## Logging And Audit

Every run should log:

- Timestamp.
- User question.
- Resolved template.
- Parameters.
- Location match result.
- Data sources used.
- Refusals/caveats.
- Runtime.
- Whether LLM was used.
- Export action if any.

Logs should avoid personal or sensitive data. For MVP, a local JSONL or SQLite log is sufficient.

## Testing Strategy

Unit tests:

- Manifest parsing.
- Schema validation.
- Caveat lookup.
- Refusal rules.
- Evidence packet validation.

Data tests:

- Row count checks.
- Required column checks.
- Date range checks.
- Null/coordinate sanity checks.
- KSI event-count tests using unique collision id.

Integration tests:

- Each query template with fixtures.
- Location resolver fallback.
- Evidence packet reproducibility.
- Export rendering.

LLM/evaluation tests:

- Unsupported recommendation prompt is refused.
- Legal/policy prompt is refused without source.
- Summary uses only packet facts.
- Missing-source question returns cannot-answer response.

Pilot acceptance tests:

- 20-30 golden questions.
- Analyst-reviewed expected outputs.
- No unsupported claims.
- Median response under 10 seconds.

## Security And Governance

MVP is internal and local-first. Still, public-sector trust requirements apply.

Governance requirements:

- Source provenance visible.
- Caveats visible.
- Method notes visible.
- Policy/legal claims blocked unless reviewed.
- Generated text clearly marked as draft.
- Pilot feedback captured.
- No public launch without governance review.

## Why Not A Vector Database Now

A vector database is not needed for the MVP because the current product is mostly structured data analysis. Policy/bylaw retrieval is planned but the corpus is not yet assembled.

Start with:

- SQL for structured data.
- Simple file-based document registry for a small policy corpus later.
- Add embeddings/vector search only when there is enough policy text to justify retrieval complexity.

## Why Not A Full Web App Now

A full production web app is premature. The MVP needs proof that analysts trust the evidence and methods. Streamlit or a simple local UI is enough for the first internal pilot.

Add FastAPI/React or shared deployment later if:

- Multiple users need shared access.
- Authentication is required.
- Export workflows become complex.
- The pilot proves repeat usage.

## Future Architecture

After pilot success, the architecture can evolve:

```text
Shared data store: PostGIS or DuckDB-backed service
API layer: FastAPI
Frontend: lightweight React/Next.js or retained Streamlit
Policy retrieval: document store + embeddings if needed
Evaluation: CI-driven golden tests and analyst review queue
Deployment: free-tier or internal hosting only after governance approval
```

## Architecture Risks

| Risk | Mitigation |
|---|---|
| Location resolver too weak | Start with constrained inputs and prioritize Centreline integration |
| LLM hallucination | Keep evidence packet as source of truth and enforce refusal policy |
| Query performance poor on raw CSV | Normalize to Parquet and DuckDB |
| Dataset versions unclear | Manifest and lock file |
| Counts disputed by analysts | Approve counting rules before pilot |
| UI hides caveats | Make caveats first-class in every output |
| Architecture grows too early | Delay services, vector DB, and production frontend |

## Initial Architecture Backlog

1. Create data source manifest.
2. Create evidence packet JSON schema.
3. Create caveat/refusal catalog.
4. Build DuckDB/Parquet ingestion for current datasets.
5. Build schema and row-count validation.
6. Build location resolver abstraction and fallback.
7. Build deterministic query runner.
8. Build MVP templates.
9. Build Streamlit evidence packet UI.
10. Build export to Markdown and JSON.
11. Add optional LLM summary adapter.
12. Add golden evaluation runner.

## Source Notes

- [City of Toronto Vision Zero Plan Overview](https://www.toronto.ca/services-payments/streets-parking-transportation/road-safety/vision-zero/vision-zero-plan-overview/)
- [City of Toronto Automated Speed Enforcement](https://www.toronto.ca/services-payments/streets-parking-transportation/road-safety/vision-zero/safety-initiatives/automated-speed-enforcement/)
- [City of Toronto Community Safety Zones](https://www.toronto.ca/services-payments/streets-parking-transportation/road-safety/vision-zero/vision-zero-dashboard/community-safety-zones-vision-zero/)
- [City of Toronto Open Data introduction](https://open.toronto.ca/docs/staff-guidance/introduction-to-open-data/)
- [Toronto Open Data Q1 2026 update](https://open.toronto.ca/quarterly-update-q1-2026/)
- [Ontario Bill 56, Building a More Competitive Economy Act, 2025](https://www.ontario.ca/laws/statute/s25011)
