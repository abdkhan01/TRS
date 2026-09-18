from __future__ import annotations

from dataclasses import dataclass
from math import cos, radians
from typing import Any


METERS_PER_DEGREE_LATITUDE = 110_540.0
METERS_PER_DEGREE_LONGITUDE = 111_320.0


@dataclass(frozen=True)
class SpatialPredicate:
    sql: str
    parameters: list[float]
    method: str


def _coordinates(location: dict[str, Any]) -> list[Any]:
    geometry = location.get("geometry") or {}
    coordinates = geometry.get("coordinates")
    if not isinstance(coordinates, list):
        raise ValueError("Resolved location has no usable coordinates")
    return coordinates


def _line_segments(location: dict[str, Any]) -> list[tuple[float, float, float, float]]:
    geometry = location.get("geometry") or {}
    geometry_type = geometry.get("type")
    coordinates = _coordinates(location)
    lines = coordinates if geometry_type == "MultiLineString" else [coordinates]
    segments: list[tuple[float, float, float, float]] = []
    for line in lines:
        if not isinstance(line, list):
            continue
        for start, end in zip(line, line[1:]):
            if len(start) >= 2 and len(end) >= 2:
                segments.append((float(start[0]), float(start[1]), float(end[0]), float(end[1])))
    if not segments:
        raise ValueError("Resolved corridor has no usable line segments")
    return segments


def spatial_predicate(
    location: dict[str, Any],
    *,
    longitude_sql: str,
    latitude_sql: str,
    buffer_meters: int,
) -> SpatialPredicate:
    """Build a parameterized local planar-distance filter for a WGS84 point column.

    The equirectangular projection is intentionally scoped to short Toronto buffers.
    It avoids a network geocoder, a spatial database service, and runtime extension
    installation while keeping the exact method visible in every packet.
    """

    if buffer_meters <= 0:
        raise ValueError("buffer_meters must be greater than zero")
    geometry = location.get("geometry") or {}
    geometry_type = geometry.get("type")
    if geometry_type == "Point":
        longitude, latitude = map(float, _coordinates(location)[:2])
        longitude_scale = METERS_PER_DEGREE_LONGITUDE * cos(radians(latitude))
        sql = f"""
        (
            power((({longitude_sql}) - ?) * ?, 2)
            + power((({latitude_sql}) - ?) * {METERS_PER_DEGREE_LATITUDE}, 2)
        ) <= power(?, 2)
        """
        return SpatialPredicate(
            sql=sql,
            parameters=[longitude, longitude_scale, latitude, float(buffer_meters)],
            method=(
                f"Point-buffer filter uses a {buffer_meters} metre local "
                "equirectangular approximation in WGS84 (EPSG:4326)."
            ),
        )

    if geometry_type not in {"LineString", "MultiLineString"}:
        raise ValueError(f"Unsupported resolved geometry type: {geometry_type}")

    clauses: list[str] = []
    parameters: list[float] = []
    for start_lon, start_lat, end_lon, end_lat in _line_segments(location):
        longitude_scale = METERS_PER_DEGREE_LONGITUDE * cos(radians((start_lat + end_lat) / 2))
        # Work in a local metre coordinate system whose origin is the segment start.
        px = f"((({longitude_sql}) - ?) * ?)"
        py = f"((({latitude_sql}) - ?) * {METERS_PER_DEGREE_LATITUDE})"
        vx = (end_lon - start_lon) * longitude_scale
        vy = (end_lat - start_lat) * METERS_PER_DEGREE_LATITUDE
        length_squared = vx * vx + vy * vy
        if length_squared == 0:
            continue
        t = f"least(1.0, greatest(0.0, (({px}) * ? + ({py}) * ?) / ?))"
        clause = f"(power(({px}) - ({t}) * ?, 2) + power(({py}) - ({t}) * ?, 2) <= power(?, 2))"
        # px/py occur once outside t and once inside t, twice for x/y distance.
        # Parameters follow the textual placeholder order in the clause.
        parameters.extend(
            [
                start_lon,
                longitude_scale,
                start_lon,
                longitude_scale,
                vx,
                start_lat,
                vy,
                length_squared,
                vx,
                start_lat,
                start_lon,
                longitude_scale,
                vx,
                start_lat,
                vy,
                length_squared,
                vy,
                float(buffer_meters),
            ]
        )
        clauses.append(clause)
    if not clauses:
        raise ValueError("Resolved corridor has no non-zero line segments")
    return SpatialPredicate(
        sql="(" + " or ".join(clauses) + ")",
        parameters=parameters,
        method=(
            f"Corridor filter measures local point-to-segment distance within {buffer_meters} metres "
            "using WGS84 (EPSG:4326) and a Toronto-scale equirectangular approximation."
        ),
    )


def json_point_expressions(column: str = '"geometry"') -> tuple[str, str]:
    return (
        f"try_cast(json_extract_string({column}, '$.coordinates[0]') as double)",
        f"try_cast(json_extract_string({column}, '$.coordinates[1]') as double)",
    )


def sources_for_location(
    source_ids: tuple[str, ...], location: dict[str, Any] | None
) -> tuple[str, ...]:
    spatial_sources = {"toronto_intersection_file", "toronto_centreline"}
    used = [item for item in source_ids if item not in spatial_sources]
    if location:
        for item in location.get("source_ids", []):
            if item not in used:
                used.append(str(item))
    return tuple(used)
