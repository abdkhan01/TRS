# Missing Data Backlog

Last updated: 2026-05-18

| Priority | Source gap | Needed for | Current MVP behavior | Candidate source |
|---|---|---|---|---|
| P0 | Toronto Centreline local copy | Corridor and segment matching. | Downloaded and profiled locally; block robust corridor queries until resolver is reviewed. | https://open.toronto.ca/dataset/toronto-centreline-tcl/ |
| P0 | Toronto Intersection File local copy | Intersection matching and confidence scoring. | Downloaded and profiled locally; use manual/constrained fallback until matching is reviewed. | https://open.toronto.ca/dataset/intersection-file-city-of-toronto/ |
| P0 | Approved KSI event counting rule | KSI event totals and trends. | Do not publish official KSI counts until approved. | Local KSI file plus analyst review |
| P1 | Complete current posted speed limits | Factual posted-speed answers. | Traffic and Parking By-Law Schedules downloaded as candidate; refuse current speed-limit answers until interpretation and matching are approved. | https://open.toronto.ca/dataset/traffic-and-parking-by-law-schedules/ |
| P1 | Structured Community Safety Zone segments/boundaries | "Is this a CSZ?" answers and ASE eligibility context. | Bylaw Schedule 33 appears in downloaded candidate data; refuse factual CSZ status until filtering, status rules, and matching are approved. | https://open.toronto.ca/dataset/traffic-and-parking-by-law-schedules/ |
| P1 | School Safety Zone structured inventory | School-zone context. | Watch Your Speed locations downloaded as partial proxy; refuse legal designation answers until authoritative SSZ inventory is approved. | https://open.toronto.ca/dataset/school-safety-zone-watch-your-speed-program-locations/ |
| P1 | Road classification structured source | Corridor comparison and context. | Candidate ArcGIS REST source registered; use KSI `ROAD_CLASS` only where present until layer is profiled. | https://gis.toronto.ca/arcgis/rest/services/cot_geospatial/FeatureServer |
| P1 | Vision Zero safety measures inventory | Intervention context. | Candidate ArcGIS REST layers registered; refuse intervention-history and before/after claims until profiled and approved. | https://gis.toronto.ca/arcgis/rest/services/cot_geospatial2/FeatureServer |
| P2 | Municipal Code/bylaw schedules | Bylaw-backed restrictions, CSZ authority, turn restrictions. | Refuse bylaw/legal authority questions. | https://www.toronto.ca/legdocs/bylaws/lawmcode.htm |
| P2 | Council/staff reports | "Why was this implemented?" policy history. | Refuse policy-history questions unless manually provided source is in packet. | Toronto Council MMIS / legdocs |
| P2 | ASE charges or violations | Enforcement volume and compliance analysis. | Downloaded monthly aggregate charges; refuse enforcement-effect claims and keep ticket-volume claims review-gated. | https://open.toronto.ca/dataset/automated-speed-enforcement-ase-charges/ |
| P2 | No-right-turn-on-red restriction inventory | Seed example around turn restrictions. | Traffic and Parking By-Law Schedules downloaded as candidate; refuse restriction status/history until no-right-turn-on-red filtering is approved. | https://open.toronto.ca/dataset/traffic-and-parking-by-law-schedules/ |

## Backlog Rules

- A missing source may still be registered in `config/data_sources.yaml` with `status: missing` or `status: registered_not_downloaded`.
- Unsupported questions must map to a refusal id in `config/refusals.yaml`.
- A source moves to `available_local` only after row count, schema, grain, date range, and limitations are documented.
