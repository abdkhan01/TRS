from __future__ import annotations

from pathlib import Path
from typing import Any

from trs.analysis.event_keys import KSI_EVENT_KEY_SQL
from trs.analysis.runner import run_query
from trs.evidence.packet import build_evidence_packet
from trs.geo.scope import json_point_expressions, sources_for_location, spatial_predicate
from trs.storage.duckdb import connect


TEMPLATE_ID = "collision_profile"

TRAFFIC_SQL = """
select
    count(distinct "_id")::integer as collision_count,
    count(distinct case when lower(trim("PEDESTRIAN")) in ('yes', 'y', 'true', '1') then "_id" end)::integer as pedestrian_collisions,
    count(distinct case when lower(trim("BICYCLE")) in ('yes', 'y', 'true', '1') then "_id" end)::integer as bicycle_collisions,
    count(distinct case when lower(trim("MOTORCYCLE")) in ('yes', 'y', 'true', '1') then "_id" end)::integer as motorcycle_collisions,
    count(distinct case when lower(trim("AUTOMOBILE")) in ('yes', 'y', 'true', '1') then "_id" end)::integer as automobile_collisions
from traffic_collisions
where try_cast("OCC_YEAR" as integer) between ? and ? {spatial_filter}
"""

KSI_DIMENSION_SQL = """
with filtered_ksi as (
    select *, extract(year from try_cast("DATE" as timestamp))::integer as collision_year
    from ksi_collisions
    where 1 = 1 {spatial_filter}
),
dimensions as (
    {dimension_unions}
)
select dimension, category, count(distinct collision_id)::integer as ksi_collision_count
from dimensions
where collision_id is not null and collision_year between ? and ?
group by dimension, category
order by dimension, ksi_collision_count desc, category
"""


def _dimension_unions(columns: set[str]) -> str:
    definitions = [
        ("light", "LIGHT"),
        ("visibility", "VISIBILITY"),
        ("impact_type", "IMPACTYPE"),
        ("severity", "ACCLASS"),
        ("road_condition", "RDSFCOND"),
    ]
    statements = [
        f'''select {KSI_EVENT_KEY_SQL} as collision_id, '{dimension}' as dimension,
                   coalesce(nullif(trim("{column}"), ''), 'Unknown') as category, collision_year
            from filtered_ksi'''
        for dimension, column in definitions
        if column in columns
    ]
    if "TIME" in columns:
        statements.append(
            f'''select {KSI_EVENT_KEY_SQL}, 'time_period',
                      case
                        when try_cast("TIME" as integer) between 600 and 1159 then 'Morning (06:00-11:59)'
                        when try_cast("TIME" as integer) between 1200 and 1759 then 'Afternoon (12:00-17:59)'
                        when try_cast("TIME" as integer) between 1800 and 2359 then 'Evening (18:00-23:59)'
                        when try_cast("TIME" as integer) between 0 and 559 then 'Overnight (00:00-05:59)'
                        else 'Unknown'
                      end as category,
                      collision_year
               from filtered_ksi'''
        )
    if not statements:
        raise ValueError("KSI source has none of the approved profile dimensions")
    return "\nunion all\n".join(statements)


def collision_profile(
    db_path: Path,
    *,
    question: str,
    start_year: int,
    end_year: int,
    buffer_meters: int = 50,
    location: dict[str, Any] | None = None,
    source_ids: tuple[str, ...] = ("traffic_collisions", "ksi_collisions"),
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
    traffic_parameters = [start_year, end_year] + (scope.parameters if scope else [])
    ksi_parameters = (scope.parameters if scope else []) + [start_year, end_year]
    traffic = run_query(db_path, TRAFFIC_SQL.format(spatial_filter=spatial_filter), traffic_parameters)
    with connect(db_path, read_only=True) as con:
        ksi_columns = {str(row[0]) for row in con.execute("describe ksi_collisions").fetchall()}
    dimensions = run_query(
        db_path,
        KSI_DIMENSION_SQL.format(
            spatial_filter=spatial_filter,
            dimension_unions=_dimension_unions(ksi_columns),
        ),
        ksi_parameters,
    )
    effective_caveats = list(caveat_ids)
    if scope and "location_match_uncertainty" not in effective_caveats:
        effective_caveats.append("location_match_uncertainty")
    traffic_row = traffic.rows[0] if traffic.rows else {}
    road_users = {
        key.removesuffix("_collisions"): value
        for key, value in traffic_row.items()
        if key.endswith("_collisions")
    }
    return build_evidence_packet(
        question=question,
        template_id=TEMPLATE_ID,
        status="answered",
        parameters={"start_year": start_year, "end_year": end_year, "buffer_meters": buffer_meters},
        results={
            "collision_count": traffic_row.get("collision_count", 0),
            "road_user_collision_counts": road_users,
            "ksi_condition_breakdown": dimensions.rows,
        },
        source_ids=sources_for_location(source_ids, location),
        methods=[
            "Traffic collision totals use distinct _id values from the event-grain candidate source.",
            "Road-user categories may overlap because a collision can involve multiple modes.",
            "Severity, time, light, visibility, road-condition, and impact breakdowns use ACCNUM when populated and a deterministic occurrence-field fallback key otherwise.",
            *([scope.method] if scope else ["No spatial filter was requested; results are citywide."]),
        ],
        caveat_ids=effective_caveats,
        location=location,
        sql_template=f"{TEMPLATE_ID}_v1",
        runtime_ms=traffic.runtime_ms + dimensions.runtime_ms,
        query_metadata={
            "traffic_sql_parameters": traffic_parameters,
            "ksi_sql_parameters": ksi_parameters,
            "spatial_filter_applied": scope is not None,
        },
        **packet_paths,
    )
