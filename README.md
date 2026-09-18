# TorontoRoadSafety

Datasets:
- Traffic Collisions: https://data.urbandatacentre.ca/en/catalogue/city-toronto-police-annual-statistical-report-traffic-collisions
- Motor Vehicle Collisions: https://data.urbandatacentre.ca/catalogue/city-toronto-motor-vehicle-collisions-involving-killed-or-seriously-injured-persons
- Automated Speed Enforcement Cameras: https://data.urbandatacentre.ca/catalogue/city-toronto-automated-speed-enforcement-locations
- Traffic Volume: https://open.toronto.ca/dataset/traffic-volumes-midblock-vehicle-speed-volume-and-classification-counts/

## Phase 1: Data Audit And Evidence Model

The approved first phase is documented in:

- `docs/phase-1-resource-audit.md`
- `docs/data-audit-template.md`
- `docs/counting-methods.md`
- `docs/evidence-model.md`
- `docs/missing-data-backlog.md`
- `config/data_sources.yaml`
- `config/caveats.yaml`
- `config/refusals.yaml`
- `schemas/evidence_packet.schema.json`
- `eval/golden_questions.yaml`

Raw datasets are large and should not be committed casually. Use `config/data_sources.yaml` as the source registry, then profile and ingest approved local files into ignored `data/` outputs during implementation.

## Evidence Engine

The local evidence engine runs approved deterministic templates from `config/templates.yaml`, validates every output against `schemas/evidence_packet.schema.json`, and renders source provenance, caveats, or refusal reasons from the tracked catalogs.

Run a citywide KSI trend against the local DuckDB database:

```bash
.venv/bin/python scripts/run_evidence.py ksi_trend \
  "Show the citywide KSI trend from 2019 to 2023" \
  --start-year 2019 --end-year 2023
```

Location-dependent templates currently return the approved `location_resolver_unavailable` refusal. Ontario Road Network tables are explicitly ineligible for evidence queries until their ingestion is corrected.

## Local Analyst UI

Install the project dependencies, ingest the local datasets, and start the Streamlit analyst interface from the repository root:

```bash
.venv/bin/pip install -r requirements.txt
.venv/bin/streamlit run scripts/run_analyst_ui.py
```

The UI uses `data/trs.duckdb` by default. Set `TRS_DB_PATH` or edit the path in the sidebar to use another local database. An optional append-only audit-log path can be supplied with `TRS_COPILOT_LOG_PATH` or in the sidebar.

The interface supports automatic question classification or an explicit evidence template, date range, optional location and buffer inputs. Every response exposes its status, evidence, refusals, source versions, location assumptions, methods, caveats, and reproducibility metadata. JSON and Markdown evidence reports are copy- and download-ready.

The UI is deliberately local and single-user for the MVP. It does not authenticate users or host data, and it does not bypass evidence-engine refusals when a reviewed source or location resolver is unavailable.
