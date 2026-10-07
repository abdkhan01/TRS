from __future__ import annotations

from pathlib import Path
from typing import Any

from trs.analysis.runner import run_query
from trs.evidence.packet import build_evidence_packet
from trs.geo.scope import json_point_expressions, sources_for_location, spatial_predicate


TRAFFIC_SQL = """
select
    count(distinct "_id")::integer as collision_count,
    count(distinct case when lower(trim("PEDESTRIAN")) in ('yes', 'y', 'true', '1') then "_id" end)::integer as pedestrian_collisions,
    count(distinct case when lower(trim("BICYCLE")) in ('yes', 'y', 'true', '1') then "_id" end)::integer as bicycle_collisions,
    count(distinct case when lower(trim("MOTORCYCLE")) in ('yes', 'y', 'true', '1') then "_id" end)::integer as motorcycle_collisions,
    count(distinct case when lower(trim("AUTOMOBILE")) in ('yes', 'y', 'true', '1') then "_id" end)::integer as automobile_collisions
from traffic_collisions
where try_cast("OCC_YEAR" as integer) between ? and ? and {spatial_filter}
"""

KSI_SQL = """
select count(distinct "ACCNUM")::integer as ksi_collision_count
from ksi_collisions
where extract(year from try_cast("DATE" as timestamp))::integer between ? and ?
  and "ACCNUM" is not null and {spatial_filter}
"""


def _snapshot(
    db_path: Path,
    *,
    template_id: str,
    question: str,
    start_year: int,
    end_year: int,
    buffer_meters: int,
    location: dict[str, Any] | None,
    source_ids: tuple[str, ...],
    caveat_ids: tuple[str, ...],
    **packet_paths: Any,
) -> dict[str, Any]:
    if start_year > end_year:
        raise ValueError("start_year must be less than or equal to end_year")
    if not location or not location.get("geometry"):
        raise ValueError("A resolved location is required for a safety snapshot")
    longitude_sql, latitude_sql = json_point_expressions()
    scope = spatial_predicate(
        location,
        longitude_sql=longitude_sql,
        latitude_sql=latitude_sql,
        buffer_meters=buffer_meters,
    )
    parameters = [start_year, end_year] + scope.parameters
    traffic = run_query(db_path, TRAFFIC_SQL.format(spatial_filter=scope.sql), parameters)
    ksi = run_query(db_path, KSI_SQL.format(spatial_filter=scope.sql), parameters)
    traffic_row = traffic.rows[0] if traffic.rows else {}
    ksi_row = ksi.rows[0] if ksi.rows else {}
    road_users = {
        key.removesuffix("_collisions"): value
        for key, value in traffic_row.items()
        if key.endswith("_collisions")
    }
    return build_evidence_packet(
        question=question,
        template_id=template_id,
        status="answered",
        parameters={"start_year": start_year, "end_year": end_year, "buffer_meters": buffer_meters},
        results={
            "collision_count": traffic_row.get("collision_count", 0),
            "ksi_collision_count": ksi_row.get("ksi_collision_count", 0),
            "road_user_collision_counts": road_users,
        },
        source_ids=sources_for_location(source_ids, location),
        methods=[
            "Traffic collision totals count distinct _id values; KSI totals count distinct ACCNUM values.",
            "Road-user categories may overlap because one event can involve multiple modes.",
            scope.method,
        ],
        caveat_ids=caveat_ids,
        location=location,
        sql_template=f"{template_id}_v1",
        runtime_ms=traffic.runtime_ms + ksi.runtime_ms,
        query_metadata={"sql_parameters": parameters, "spatial_filter_applied": True},
        **packet_paths,
    )


def intersection_snapshot(
    db_path: Path,
    *,
    question: str,
    start_year: int,
    end_year: int,
    buffer_meters: int = 50,
    location: dict[str, Any] | None = None,
    source_ids: tuple[str, ...] = ("traffic_collisions", "ksi_collisions", "toronto_intersection_file"),
    caveat_ids: tuple[str, ...] = (
        "ksi_party_grain",
        "counting_rules_unapproved",
        "descriptive_not_causal",
        "location_match_uncertainty",
    ),
    **packet_paths: Any,
) -> dict[str, Any]:
    return _snapshot(
        db_path,
        template_id="intersection_safety_snapshot",
        question=question,
        start_year=start_year,
        end_year=end_year,
        buffer_meters=buffer_meters,
        location=location,
        source_ids=source_ids,
        caveat_ids=caveat_ids,
        **packet_paths,
    )


def corridor_snapshot(
    db_path: Path,
    *,
    question: str,
    start_year: int,
    end_year: int,
    buffer_meters: int = 25,
    location: dict[str, Any] | None = None,
    source_ids: tuple[str, ...] = ("traffic_collisions", "ksi_collisions", "toronto_centreline"),
    caveat_ids: tuple[str, ...] = (
        "ksi_party_grain",
        "counting_rules_unapproved",
        "descriptive_not_causal",
        "location_match_uncertainty",
        "corridor_scope_approximation",
    ),
    **packet_paths: Any,
) -> dict[str, Any]:
    geometry_type = ((location or {}).get("geometry") or {}).get("type")
    if geometry_type not in {"LineString", "MultiLineString"}:
        raise ValueError("Corridor snapshot requires a resolved corridor location")
    return _snapshot(
        db_path,
        template_id="corridor_safety_snapshot",
        question=question,
        start_year=start_year,
        end_year=end_year,
        buffer_meters=buffer_meters,
        location=location,
        source_ids=source_ids,
        caveat_ids=caveat_ids,
        **packet_paths,
    )
