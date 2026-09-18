from __future__ import annotations

from pathlib import Path
from typing import Any

from trs.analysis.event_keys import KSI_EVENT_KEY_SQL
from trs.analysis.runner import run_query
from trs.evidence.packet import build_evidence_packet


TEMPLATE_ID = "ksi_trend"
SQL = f"""
with event_years as (
    select
        {KSI_EVENT_KEY_SQL} as collision_id,
        extract(year from try_cast("DATE" as timestamp))::integer as collision_year
    from ksi_collisions
)
select
    collision_year as year,
    count(distinct collision_id)::integer as ksi_collision_count
from event_years
where collision_year between ? and ?
group by collision_year
order by collision_year
"""


def ksi_trend(
    db_path: Path,
    *,
    question: str,
    start_year: int,
    end_year: int,
    location: dict[str, Any] | None = None,
    source_ids: tuple[str, ...] = ("ksi_collisions",),
    caveat_ids: tuple[str, ...] = (
        "ksi_party_grain",
        "counting_rules_unapproved",
        "descriptive_not_causal",
    ),
    **packet_paths: Any,
) -> dict[str, Any]:
    if start_year > end_year:
        raise ValueError("start_year must be less than or equal to end_year")
    query = run_query(db_path, SQL, [start_year, end_year])
    total = sum(int(row["ksi_collision_count"]) for row in query.rows)
    return build_evidence_packet(
        question=question,
        template_id=TEMPLATE_ID,
        status="answered",
        parameters={"start_year": start_year, "end_year": end_year},
        results={"series": query.rows, "ksi_collision_count": total},
        source_ids=source_ids,
        methods=[
            "KSI collision events use ACCNUM when populated; records without a usable ACCNUM use a deterministic DATE, TIME, STREET1, STREET2, and geometry fallback key.",
            "The year is extracted from DATE and filtered inclusively.",
        ],
        caveat_ids=caveat_ids,
        location=location,
        sql_template=f"{TEMPLATE_ID}_v1",
        runtime_ms=query.runtime_ms,
        query_metadata={"sql_parameters": [start_year, end_year]},
        **packet_paths,
    )
