from __future__ import annotations

from pathlib import Path
from typing import Any

from trs.analysis.runner import run_query
from trs.evidence.packet import build_evidence_packet
from trs.geo.scope import json_point_expressions, sources_for_location, spatial_predicate


SQL = """
select
    "FID" as fid,
    "location" as location_name,
    "Status" as source_status,
    try_cast(json_extract_string("geometry", '$.coordinates[0]') as double) as longitude,
    try_cast(json_extract_string("geometry", '$.coordinates[1]') as double) as latitude
from automated_speed_enforcement_locations
where {spatial_filter}
order by "FID"
"""


def historical_ase_context(
    db_path: Path,
    *,
    question: str,
    buffer_meters: int = 250,
    location: dict[str, Any] | None = None,
    source_ids: tuple[str, ...] = ("automated_speed_enforcement_locations", "toronto_intersection_file"),
    caveat_ids: tuple[str, ...] = ("ase_historical_context_only", "ase_locations_not_charges", "location_match_uncertainty"),
    **packet_paths: Any,
) -> dict[str, Any]:
    if not location or not location.get("geometry"):
        raise ValueError("A resolved location is required for historical ASE context")
    longitude_sql, latitude_sql = json_point_expressions()
    scope = spatial_predicate(
        location,
        longitude_sql=longitude_sql,
        latitude_sql=latitude_sql,
        buffer_meters=buffer_meters,
    )
    query = run_query(db_path, SQL.format(spatial_filter=scope.sql), scope.parameters)
    return build_evidence_packet(
        question=question,
        template_id="historical_ase_context",
        status="answered",
        parameters={"buffer_meters": buffer_meters},
        results={"camera_location_count": len(query.rows), "camera_locations": query.rows},
        source_ids=sources_for_location(source_ids, location),
        methods=["Records are historical camera-location rows, not charges, violations, or effects.", scope.method],
        caveat_ids=caveat_ids,
        location=location,
        sql_template="historical_ase_context_v1",
        runtime_ms=query.runtime_ms,
        query_metadata={"sql_parameters": scope.parameters, "spatial_filter_applied": True},
        **packet_paths,
    )
