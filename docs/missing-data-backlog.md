# Missing Data Backlog

Last updated: 2026-05-18

| Priority | Source gap | Needed for | Current MVP behavior | Candidate source |
|---|---|---|---|---|
| P0 | Toronto Centreline local copy | Corridor and segment matching. | Register source; block robust corridor queries until profiled. | https://open.toronto.ca/dataset/toronto-centreline-tcl/ |
| P0 | Toronto Intersection File local copy | Intersection matching and confidence scoring. | Register source; use manual/constrained fallback only. | https://data.urbandatacentre.ca/catalogue/city-toronto-intersection-file-city-of-toronto |
| P0 | Approved KSI event counting rule | KSI event totals and trends. | Do not publish official KSI counts until approved. | Local KSI file plus analyst review |
| P1 | Complete current posted speed limits | Factual posted-speed answers. | Refuse current speed-limit answers. | To investigate; area reductions are not enough until verified |
| P1 | Structured Community Safety Zone segments/boundaries | "Is this a CSZ?" answers and ASE eligibility context. | Refuse factual CSZ status; cite missing structured authority. | City CSZ page, Municipal Code, possible internal GIS |
| P1 | School Safety Zone structured inventory | School-zone context. | Refuse legal designation answers; allow only sourced context if registered. | City Vision Zero School Safety Zones page |
| P1 | Road classification structured source | Corridor comparison and context. | Use KSI `ROAD_CLASS` only where present; caveat incompleteness. | Centreline attributes and Road Classification System |
| P1 | Vision Zero safety measures inventory | Intervention context. | Refuse intervention-history and before/after claims. | Vision Zero Mapping Tool / internal Transportation Services data |
| P2 | Municipal Code/bylaw schedules | Bylaw-backed restrictions, CSZ authority, turn restrictions. | Refuse bylaw/legal authority questions. | https://www.toronto.ca/legdocs/bylaws/lawmcode.htm |
| P2 | Council/staff reports | "Why was this implemented?" policy history. | Refuse policy-history questions unless manually provided source is in packet. | Toronto Council MMIS / legdocs |
| P2 | ASE charges or violations | Enforcement volume and compliance analysis. | Refuse enforcement-effect and ticket-volume claims. | No reliable current open source confirmed |
| P2 | No-right-turn-on-red restriction inventory | Seed example around turn restrictions. | Refuse restriction status/history unless source is added. | To investigate |

## Backlog Rules

- A missing source may still be registered in `config/data_sources.yaml` with `status: missing` or `status: registered_not_downloaded`.
- Unsupported questions must map to a refusal id in `config/refusals.yaml`.
- A source moves to `available_local` only after row count, schema, grain, date range, and limitations are documented.
