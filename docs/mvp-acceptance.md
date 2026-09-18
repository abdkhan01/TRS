# MVP Acceptance Record

Last updated: 2026-09-18

## Implemented boundary

The local MVP is the narrowed Vision Zero Evidence Copilot defined by the feasibility, development-plan, and software-architecture documents. It is an evidence product, not a legal, causal, policy-rationale, or recommendation engine.

Implemented capabilities:

- Registered local source ingestion into Parquet and DuckDB with a manifest lock.
- Local intersection, manual-coordinate, and named-corridor resolution.
- A documented 2019-2023 default window for safety snapshots when no period is supplied.
- Intersection/corridor safety snapshots, KSI trends, collision profiles, historical ASE context, and observed speed/volume context.
- Schema-validated evidence packets with sources, versions/dates, methods, caveats, refusals, spatial assumptions, and runtimes.
- Deterministic natural-language routing, parameter extraction, packet-only summaries, append-only audit events, and 20 golden questions.
- Local Streamlit analyst workflow with visible refusal/error states and JSON/Markdown exports.

## Automated release checks

- Full pytest suite passes.
- Intent-only golden evaluation passes 20/20.
- Full real-data golden evaluation passes 20/20.
- All supported packets validate against `schemas/evidence_packet.schema.json`.
- All unsupported legal/policy/causal/recommendation questions return approved refusals.
- Real-data factual query runtimes remain below the documented 10-second target on the development laptop.

## Human approval still required

The build can be used as a local pilot, but these governance gates cannot be completed by code:

- Approve the hybrid KSI event key, including its fallback for 2015-2019 rows without usable `ACCNUM`.
- Approve traffic-collision grain and official severity/road-user definitions.
- Approve the 50-metre intersection default and Centreline corridor method.
- Review caveat and refusal wording before official reuse.
- Conduct analyst spot checks and the documented pilot acceptance review.

## Architecture improvement recommended

The next refactor should introduce a single environment-aware runtime settings object for the database, manifest, processed-data root, and audit path. The MVP already supports `TRS_DB_PATH`, but one settings boundary would make worktrees and later shared deployment cleaner without adding a service or changing the deterministic evidence contract.
