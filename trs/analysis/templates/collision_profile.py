from __future__ import annotations

from pathlib import Path
from typing import Any

from trs.analysis.event_keys import KSI_EVENT_KEY_SQL
from trs.analysis.runner import run_query
from trs.evidence.packet import build_evidence_packet


TEMPLATE_ID = "collision_profile"

TRAFFIC_SQL = """
select
    count(distinct "_id")::integer as collision_count,
    count(distinct case when lower(trim("PEDESTRIAN")) in ('yes', 'y', 'true', '1') then "_id" end)::integer as pedestrian_collisions,
    count(distinct case when lower(trim("BICYCLE")) in ('yes', 'y', 'true', '1') then "_id" end)::integer as bicycle_collisions,
    count(distinct case when lower(trim("MOTORCYCLE")) in ('yes', 'y', 'true', '1') then "_id" end)::integer as motorcycle_collisions,
    count(distinct case when lower(trim("AUTOMOBILE")) in ('yes', 'y', 'true', '1') then "_id" end)::integer as automobile_collisions
from traffic_collisions
where try_cast("OCC_YEAR" as integer) between ? and ?
"""

KSI_DIMENSION_SQL = f"""
select
    dimension,
    category,
    count(distinct collision_id)::integer as ksi_collision_count
from (
    select {KSI_EVENT_KEY_SQL} as collision_id, 'light' as dimension, coalesce(nullif(trim("LIGHT"), ''), 'Unknown') as category,
           extract(year from try_cast("DATE" as timestamp))::integer as collision_year
    from ksi_collisions
    union all
    select {KSI_EVENT_KEY_SQL}, 'visibility', coalesce(nullif(trim("VISIBILITY"), ''), 'Unknown'),
           extract(year from try_cast("DATE" as timestamp))::integer
    from ksi_collisions
    union all
    select {KSI_EVENT_KEY_SQL}, 'impact_type', coalesce(nullif(trim("IMPACTYPE"), ''), 'Unknown'),
           extract(year from try_cast("DATE" as timestamp))::integer
    from ksi_collisions
) dimensions
where collision_id is not null and collision_year between ? and ?
group by dimension, category
order by dimension, ksi_collision_count desc, category
"""


def collision_profile(
    db_path: Path,
    *,
    question: str,
    start_year: int,
    end_year: int,
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
    traffic = run_query(db_path, TRAFFIC_SQL, [start_year, end_year])
    dimensions = run_query(db_path, KSI_DIMENSION_SQL, [start_year, end_year])
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
        parameters={"start_year": start_year, "end_year": end_year},
        results={
            "collision_count": traffic_row.get("collision_count", 0),
            "road_user_collision_counts": road_users,
            "ksi_condition_breakdown": dimensions.rows,
        },
        source_ids=source_ids,
        methods=[
            "Traffic collision totals use distinct _id values from the event-grain candidate source.",
            "Road-user categories may overlap because a collision can involve multiple modes.",
            "KSI breakdowns use ACCNUM when populated and a deterministic occurrence-field fallback key otherwise.",
        ],
        caveat_ids=caveat_ids,
        location=location,
        sql_template=f"{TEMPLATE_ID}_v1",
        runtime_ms=traffic.runtime_ms + dimensions.runtime_ms,
        query_metadata={"sql_parameters": [start_year, end_year]},
        **packet_paths,
    )
