from __future__ import annotations

from pathlib import Path
from typing import Any

from trs.analysis.runner import run_query
from trs.evidence.packet import build_evidence_packet
from trs.geo.scope import sources_for_location, spatial_predicate


SQL = """
select
    "latest_count_id" as count_id,
    "latest_count_type" as count_type,
    "latest_count_date_start" as date_start,
    "latest_count_date_end" as date_end,
    "location_name",
    try_cast("longitude" as double) as longitude,
    try_cast("latitude" as double) as latitude,
    try_cast("avg_daily_vol" as double) as average_daily_volume,
    try_cast("avg_weekday_daily_vol" as double) as average_weekday_daily_volume,
    try_cast("avg_weekend_daily_vol" as double) as average_weekend_daily_volume,
    try_cast("avg_speed" as double) as average_observed_speed,
    try_cast("avg_85th_percentile_speed" as double) as observed_85th_percentile_speed,
    try_cast("avg_95th_percentile_speed" as double) as observed_95th_percentile_speed
from traffic_volume_summary
where {spatial_filter}
order by try_cast("latest_count_date_start" as date) desc nulls last, "latest_count_id"
limit ?
"""


def speed_volume_context(
    db_path: Path,
    *,
    question: str,
    buffer_meters: int = 500,
    limit: int = 20,
    location: dict[str, Any] | None = None,
    source_ids: tuple[str, ...] = ("traffic_volume", "toronto_centreline"),
    caveat_ids: tuple[str, ...] = (
        "traffic_volume_coverage_uneven",
        "observed_speed_not_posted_limit",
        "descriptive_not_causal",
        "location_match_uncertainty",
    ),
    **packet_paths: Any,
) -> dict[str, Any]:
    if not 1 <= limit <= 100:
        raise ValueError("limit must be between 1 and 100")
    if not location or not location.get("geometry"):
        raise ValueError("A resolved location is required for speed/volume context")
    scope = spatial_predicate(
        location,
        longitude_sql='try_cast("longitude" as double)',
        latitude_sql='try_cast("latitude" as double)',
        buffer_meters=buffer_meters,
    )
    parameters = scope.parameters + [limit]
    query = run_query(db_path, SQL.format(spatial_filter=scope.sql), parameters)
    return build_evidence_packet(
        question=question,
        template_id="speed_volume_context",
        status="answered",
        parameters={"buffer_meters": buffer_meters, "limit": limit},
        results={"observation_count": len(query.rows), "observations": query.rows},
        source_ids=sources_for_location(source_ids, location),
        methods=[
            "Each result is a registered latest-count summary observation; absent coverage is not inferred as zero.",
            "Speed values are observed measurements, not posted speed limits.",
            scope.method,
        ],
        caveat_ids=caveat_ids,
        location=location,
        sql_template="speed_volume_context_v1",
        runtime_ms=query.runtime_ms,
        query_metadata={"sql_parameters": parameters, "spatial_filter_applied": True},
        **packet_paths,
    )
