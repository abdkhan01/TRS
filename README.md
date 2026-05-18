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
