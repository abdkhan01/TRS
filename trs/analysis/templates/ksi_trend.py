from __future__ import annotations

from pathlib import Path
from typing import Any

from trs.analysis.runner import run_query
from trs.evidence.packet import build_evidence_packet
from trs.geo.scope import json_point_expressions, sources_for_location, spatial_predicate


TEMPLATE_ID = "ksi_trend"
SQL = """
with event_years as (
    select
        "ACCNUM" as collision_id,
        extract(year from try_cast("DATE" as timestamp))::integer as collision_year
    from ksi_collisions
    where "ACCNUM" is not null {spatial_filter}
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
    buffer_meters: int = 50,
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
    scope = None
    if location and location.get("geometry"):
        longitude_sql, latitude_sql = json_point_expressions()
        scope = spatial_predicate(
            location,
            longitude_sql=longitude_sql,
            latitude_sql=latitude_sql,
            buffer_meters=buffer_meters,
        )
    spatial_filter = f"and {scope.sql}" if scope else ""
    query_parameters = (scope.parameters if scope else []) + [start_year, end_year]
    query = run_query(db_path, SQL.format(spatial_filter=spatial_filter), query_parameters)
    total = sum(int(row["ksi_collision_count"]) for row in query.rows)
    effective_caveats = list(caveat_ids)
    if scope and "location_match_uncertainty" not in effective_caveats:
        effective_caveats.append("location_match_uncertainty")
    return build_evidence_packet(
        question=question,
        template_id=TEMPLATE_ID,
        status="answered",
        parameters={"start_year": start_year, "end_year": end_year, "buffer_meters": buffer_meters},
        results={"series": query.rows, "ksi_collision_count": total},
        source_ids=sources_for_location(source_ids, location),
        methods=[
            "KSI collision events are counted as distinct ACCNUM values.",
            "The year is extracted from DATE and filtered inclusively.",
            *([scope.method] if scope else ["No spatial filter was requested; results are citywide."]),
        ],
        caveat_ids=effective_caveats,
        location=location,
        sql_template=f"{TEMPLATE_ID}_v1",
        runtime_ms=query.runtime_ms,
        query_metadata={"sql_parameters": query_parameters, "spatial_filter_applied": scope is not None},
        **packet_paths,
    )
