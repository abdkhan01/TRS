from __future__ import annotations

import json
import re
from collections import deque
from pathlib import Path
from typing import Any

import duckdb

from trs.geo.reference import canonical_street_name
from trs.storage.duckdb import connect


class LocationResolutionError(ValueError):
    """Raised when a requested local location cannot be resolved safely."""


class LocationResolver:
    """Small orchestration-facing wrapper around the structured resolver API."""

    def __init__(self, db_path: Path):
        self.db_path = Path(db_path)

    def resolve(self, text: str) -> dict[str, Any]:
        corridor = _CORRIDOR_TEXT.match(text)
        if corridor:
            street = corridor.group("street").strip()
            start = corridor.group("start").strip()
            end = corridor.group("end").strip()
            return resolve_location(
                self.db_path,
                {
                    "type": "corridor",
                    "input": text,
                    "street_name": street,
                    "start": {"input": f"{street} and {start}"},
                    "end": {"input": f"{street} and {end}"},
                },
            )
        return resolve_location(
            self.db_path,
            {"type": "intersection", "input": text},
        )


_SEPARATOR = re.compile(r"\s*(?:/|&|\band\b|\bat\b)\s*", re.IGNORECASE)
_CORRIDOR_TEXT = re.compile(
    r"^\s*(?P<street>.+?)\s+from\s+(?P<start>.+?)\s+to\s+(?P<end>.+?)\s*$",
    re.IGNORECASE,
)


def _normalise(value: str) -> str:
    return canonical_street_name(value)


def _street_parts(value: str) -> list[str]:
    return [_normalise(part) for part in _SEPARATOR.split(value) if _normalise(part)]


def _point(longitude: float, latitude: float) -> list[float]:
    if not (-180 <= longitude <= 180 and -90 <= latitude <= 90):
        raise LocationResolutionError("Manual coordinates are outside valid WGS84 bounds")
    return [longitude, latitude]


def _geometry_payload(geometry: str | dict[str, Any]) -> dict[str, Any]:
    payload = json.loads(geometry) if isinstance(geometry, str) else geometry
    if not isinstance(payload, dict):
        raise LocationResolutionError("Location geometry is not a GeoJSON object")
    return payload


def _first_point(geometry: dict[str, Any]) -> list[float]:
    coordinates = geometry.get("coordinates")
    while isinstance(coordinates, list) and coordinates and isinstance(coordinates[0], list):
        coordinates = coordinates[0]
    if not isinstance(coordinates, list) or len(coordinates) < 2:
        raise LocationResolutionError("Location source has unusable coordinates")
    return _point(float(coordinates[0]), float(coordinates[1]))


def _manual_point(spec: dict[str, Any]) -> dict[str, Any] | None:
    longitude = spec.get("longitude", spec.get("lon"))
    latitude = spec.get("latitude", spec.get("lat"))
    if longitude is None or latitude is None:
        geometry = spec.get("geometry")
        if isinstance(geometry, dict) and geometry.get("type") == "Point":
            longitude, latitude = geometry.get("coordinates", [None, None])[:2]
    if longitude is None or latitude is None:
        return None
    coordinates = _point(float(longitude), float(latitude))
    return {
        "input": str(spec.get("input", f"{coordinates[1]}, {coordinates[0]}")),
        "resolved_name": str(spec.get("resolved_name") or "Manual coordinates"),
        "geometry": {"type": "Point", "coordinates": coordinates, "crs": "EPSG:4326"},
        "crs": "EPSG:4326",
        "match_confidence": "manual_or_verified",
        "method": "Analyst-supplied WGS84 coordinates; no geocoder was used.",
        "source_ids": [],
    }


def _placeholders(values: set[str]) -> str:
    return ", ".join("?" for _ in values)


def _street_id_candidates(
    con: duckdb.DuckDBPyConnection,
    requested: list[str],
) -> list[set[str]]:
    candidates: list[set[str]] = []
    for part in requested:
        rows = con.execute(
            "select distinct street_id from location_street_alias where alias = ?",
            [part],
        ).fetchall()
        street_ids = {str(row[0]) for row in rows}
        if not street_ids:
            raise LocationResolutionError(f"No canonical Toronto street matched '{part}'")
        candidates.append(street_ids)
    return candidates


def _canonical_intersection_rows(
    con: duckdb.DuckDBPyConnection,
    requested: list[str],
) -> list[tuple[str, str, str]]:
    street_id_sets = _street_id_candidates(con, requested)
    all_street_ids = set().union(*street_id_sets)
    relationship_rows = con.execute(
        f"""
        select intersection_id, street_id
        from location_intersection_street
        where street_id in ({_placeholders(all_street_ids)})
        """,
        sorted(all_street_ids),
    ).fetchall()
    by_intersection: dict[str, set[str]] = {}
    for intersection_id, street_id in relationship_rows:
        by_intersection.setdefault(str(intersection_id), set()).add(str(street_id))
    intersection_ids = {
        intersection_id
        for intersection_id, available in by_intersection.items()
        if all(available & candidates for candidates in street_id_sets)
    }
    if not intersection_ids:
        return []
    return [
        (str(row[0]), str(row[1]), str(row[2]))
        for row in con.execute(
            f"""
            select intersection_id, official_description, geometry
            from location_intersection
            where intersection_id in ({_placeholders(intersection_ids)})
            order by intersection_id
            """,
            sorted(intersection_ids),
        ).fetchall()
    ]


def _intersection(db_path: Path, spec: dict[str, Any]) -> dict[str, Any]:
    input_text = str(spec.get("input", "")).strip()
    if not input_text:
        raise LocationResolutionError("Named intersection input is empty")
    requested = _street_parts(input_text)
    if not requested:
        raise LocationResolutionError("Named intersection has no searchable street name")
    with connect(db_path, read_only=True) as con:
        try:
            rows = _canonical_intersection_rows(con, requested)
        except duckdb.CatalogException as exc:
            raise LocationResolutionError(
                "Canonical location reference tables are unavailable; rerun ingestion and view creation"
            ) from exc

    candidates: list[tuple[str, str, list[float]]] = []
    for intersection_id, description, geometry in rows:
        candidates.append((str(intersection_id), str(description), _first_point(_geometry_payload(geometry))))
    if not candidates:
        raise LocationResolutionError(f"No local intersection matched '{input_text}'")
    unique_points = {(round(item[2][0], 7), round(item[2][1], 7)) for item in candidates}
    if len(unique_points) > 1:
        names = ", ".join(item[1] for item in candidates[:5])
        raise LocationResolutionError(
            f"More than one canonical intersection matched '{input_text}': {names}"
        )
    intersection_id, description, coordinates = candidates[0]
    return {
        "input": input_text,
        "resolved_name": description,
        "geometry": {"type": "Point", "coordinates": coordinates, "crs": "EPSG:4326"},
        "crs": "EPSG:4326",
        "match_confidence": "high",
        "method": (
            "Canonical street aliases matched official LINEAR_NAME_ID values; "
            "their shared INTERSECTION_ID selected Toronto Intersection File geometry."
        ),
        "intersection_id": intersection_id,
        "source_ids": ["toronto_intersection_file"],
        "alternative_count": 0,
    }


def _resolve_point(db_path: Path, spec: dict[str, Any]) -> dict[str, Any]:
    manual = _manual_point(spec)
    return manual if manual is not None else _intersection(db_path, spec)


def _centreline_route(
    db_path: Path,
    start: dict[str, Any],
    end: dict[str, Any],
    street_name: str | None,
) -> tuple[list[list[list[float]]], list[str], str] | None:
    start_id = start.get("intersection_id")
    end_id = end.get("intersection_id")
    if not start_id or not end_id:
        return None
    with connect(db_path, read_only=True) as con:
        if street_name:
            try:
                target_ids = _street_id_candidates(con, [_normalise(street_name)])[0]
            except (duckdb.CatalogException, LocationResolutionError):
                return None
        else:
            rows = con.execute(
                """
                select street_id
                from location_intersection_street
                where intersection_id in (?, ?)
                group by street_id
                having count(distinct intersection_id) = 2
                """,
                [str(start_id), str(end_id)],
            ).fetchall()
            target_ids = {str(row[0]) for row in rows}
        if not target_ids:
            return None
        rows = con.execute(
            """
            select "CENTRELINE_ID", "LINEAR_NAME_ID", "LINEAR_NAME_FULL", "FROM_INTERSECTION_ID",
                   "TO_INTERSECTION_ID", "geometry"
            from toronto_centreline
            where "geometry" is not null
            """
        ).fetchall()
    edges: dict[str, list[tuple[str, str, str, str]]] = {}
    for segment_id, street_id, name, from_id, to_id, geometry in rows:
        if str(street_id) not in target_ids or not from_id or not to_id:
            continue
        edge = (str(to_id), str(segment_id), str(geometry), str(name))
        edges.setdefault(str(from_id), []).append(edge)
        reverse = (str(from_id), str(segment_id), str(geometry), str(name))
        edges.setdefault(str(to_id), []).append(reverse)

    queue = deque([str(start_id)])
    previous: dict[str, tuple[str, str, str, str] | None] = {str(start_id): None}
    while queue:
        node = queue.popleft()
        if node == str(end_id):
            break
        for next_node, segment_id, geometry, name in edges.get(node, []):
            if next_node not in previous:
                previous[next_node] = (node, segment_id, geometry, name)
                queue.append(next_node)
    if str(end_id) not in previous:
        return None

    route: list[tuple[str, str, str]] = []
    node = str(end_id)
    while previous[node] is not None:
        prior, segment_id, geometry, name = previous[node]  # type: ignore[misc]
        route.append((segment_id, geometry, name))
        node = prior
    route.reverse()
    lines: list[list[list[float]]] = []
    for _, geometry, _ in route:
        payload = _geometry_payload(geometry)
        coordinates = payload.get("coordinates", [])
        if payload.get("type") == "LineString":
            coordinates = [coordinates]
        for line in coordinates:
            if isinstance(line, list) and len(line) >= 2:
                lines.append([[float(point[0]), float(point[1])] for point in line])
    if not lines:
        return None
    return lines, [item[0] for item in route], route[0][2]


def _corridor(db_path: Path, spec: dict[str, Any]) -> dict[str, Any]:
    start_spec = spec.get("start")
    end_spec = spec.get("end")
    if not isinstance(start_spec, dict) or not isinstance(end_spec, dict):
        raise LocationResolutionError("Corridor location requires start and end location objects")
    start = _resolve_point(db_path, start_spec)
    end = _resolve_point(db_path, end_spec)
    route = _centreline_route(db_path, start, end, spec.get("street_name"))
    source_ids = list(dict.fromkeys(start.get("source_ids", []) + end.get("source_ids", [])))
    if route:
        lines, segment_ids, matched_name = route
        source_ids.append("toronto_centreline")
        geometry: dict[str, Any] = {"type": "MultiLineString", "coordinates": lines, "crs": "EPSG:4326"}
        confidence = "high" if start["match_confidence"] == end["match_confidence"] == "high" else "medium"
        method = f"Endpoints resolved locally; connected '{matched_name}' Toronto Centreline segments were selected."
    else:
        segment_ids = []
        geometry = {
            "type": "LineString",
            "coordinates": [start["geometry"]["coordinates"], end["geometry"]["coordinates"]],
            "crs": "EPSG:4326",
        }
        confidence = "low"
        method = "Endpoints resolved locally; no connected Centreline route matched, so a straight endpoint line was used."
    return {
        "input": str(spec.get("input", "Corridor endpoints")),
        "resolved_name": str(spec.get("resolved_name") or f"{start['resolved_name']} to {end['resolved_name']}"),
        "geometry": geometry,
        "crs": "EPSG:4326",
        "match_confidence": confidence,
        "method": method,
        "source_ids": list(dict.fromkeys(source_ids)),
        "start": start,
        "end": end,
        "centreline_ids": segment_ids,
    }


def resolve_location(db_path: Path, spec: dict[str, Any]) -> dict[str, Any]:
    """Resolve an analyst-controlled location using only the local DuckDB sources."""

    if not isinstance(spec, dict):
        raise LocationResolutionError("Location must be an object")
    location_type = str(spec.get("type", "point")).lower()
    if location_type == "corridor" or ("start" in spec and "end" in spec):
        return _corridor(db_path, spec)
    if location_type not in {"point", "intersection"}:
        raise LocationResolutionError(f"Unsupported location type: {location_type}")
    return _resolve_point(db_path, spec)
