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

Implemented templates cover citywide or location-scoped KSI trends and collision profiles, intersection and corridor snapshots, historical ASE context, and observed speed/volume context. Current posted-speed, CSZ, legal/policy, causal, and recommendation requests remain explicit refusals. Ontario Road Network tables are ineligible for evidence queries until their ingestion is corrected.

## Local Analyst UI

Create a Python 3.12 virtual environment, install dependencies, ingest the registered local datasets, and start the Streamlit analyst interface from the repository root:

```bash
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m trs.ingest.cli all
.venv/bin/python -m trs.ingest.cli verify
.venv/bin/streamlit run scripts/run_analyst_ui.py
```

If `.venv` does not exist yet, create it with `python3.12 -m venv .venv`. Raw source files must remain under the ignored `datasets/` paths registered in `config/data_sources.yaml`.

The UI uses `data/trs.duckdb` by default. Set `TRS_DB_PATH` or edit the path in the sidebar to use another local database. Query and export events are written to the ignored local path `data/audit/copilot.jsonl` by default; override it with `TRS_COPILOT_LOG_PATH` or in the sidebar.

The interface supports automatic question classification or an explicit evidence template, date range, optional location and buffer inputs. Named intersections use forms such as `King St W and Spadina Ave`; corridors use `King St W from Spadina Ave to Bathurst St`. Every response exposes its status, evidence, refusals, source versions, location assumptions, methods, caveats, and reproducibility metadata. JSON and Markdown evidence reports are copy- and download-ready.

During `create-views` (and therefore `all`), the ingestion pipeline also builds
local canonical street and intersection reference tables from Toronto
Centreline IDs and endpoint relationships. Street-name normalization supports
lookup variants such as `St`/`Street`, but official IDs—not parsed strings—own
location identity. Only a unique high-confidence canonical match or
analyst-supplied coordinates can proceed to a location-scoped evidence query.

The UI is deliberately local and single-user for the MVP. It does not authenticate users or host data, and it does not bypass evidence-engine refusals when a reviewed source or location resolver is unavailable.

Run the 20-question routing and end-to-end evaluation suites with:

```bash
.venv/bin/python scripts/run_golden_eval.py --intent-only
.venv/bin/python scripts/run_golden_eval.py --audit-log data/audit/golden.jsonl
```

The MVP remains descriptive and provisional. KSI coverage ends in 2023, the hybrid KSI event key and default spatial methods still require analyst approval, location matching is local rather than a general geocoder, and observed speeds are not posted speed limits.
