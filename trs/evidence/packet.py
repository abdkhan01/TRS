from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from trs.evidence.catalog import manifest_version, render_caveats, render_refusals, source_metadata
from trs.evidence.schema import validate_packet


def unresolved_location(input_text: str = "Toronto citywide") -> dict[str, Any]:
    return {
        "input": input_text,
        "resolved_name": None,
        "geometry": None,
        "geometry_type": "unresolved",
        "source_ids": [],
        "match_confidence": "unresolved",
        "method": "No location resolver applied; results are citywide.",
    }


def normalise_location(location: dict[str, Any] | None) -> dict[str, Any]:
    """Complete the public location contract for legacy and resolver payloads."""
    if location is None:
        return unresolved_location()

    normalised = dict(location)
    geometry = normalised.get("geometry")
    geojson_type = geometry.get("type") if isinstance(geometry, dict) else None
    if normalised.get("geometry_type") not in {
        "point", "intersection", "segment", "corridor", "polygon", "unresolved"
    }:
        if normalised.get("intersection_id"):
            normalised["geometry_type"] = "intersection"
        elif geojson_type in {"LineString", "MultiLineString"}:
            normalised["geometry_type"] = "corridor"
        elif geojson_type in {"Polygon", "MultiPolygon"}:
            normalised["geometry_type"] = "polygon"
        elif geojson_type == "Point":
            normalised["geometry_type"] = "point"
        else:
            normalised["geometry_type"] = "unresolved"
    normalised["source_ids"] = list(dict.fromkeys(str(item) for item in normalised.get("source_ids", [])))
    normalised.setdefault("input", "")
    normalised.setdefault("resolved_name", None)
    normalised.setdefault("match_confidence", "unresolved")
    normalised.setdefault("method", "No location-resolution method was recorded.")
    return normalised


def build_evidence_packet(
    *,
    question: str,
    template_id: str,
    status: str,
    parameters: dict[str, Any] | None = None,
    results: dict[str, Any] | None = None,
    source_ids: list[str] | tuple[str, ...] = (),
    methods: list[str] | tuple[str, ...] = (),
    caveat_ids: list[str] | tuple[str, ...] = (),
    refusal_ids: list[str] | tuple[str, ...] = (),
    location: dict[str, Any] | None = None,
    sql_template: str | None = None,
    runtime_ms: float | None = None,
    query_metadata: dict[str, Any] | None = None,
    registry_path: Path | None = None,
    caveats_path: Path | None = None,
    refusals_path: Path | None = None,
    lock_path: Path | None = None,
    schema_path: Path | None = None,
    packet_id: str | None = None,
    created_at: str | None = None,
) -> dict[str, Any]:
    metadata = {
        "sql_template": sql_template,
        "runtime_ms": runtime_ms,
        "data_manifest_version": manifest_version(lock_path),
    }
    metadata.update(query_metadata or {})
    packet = {
        "packet_id": packet_id or str(uuid4()),
        "created_at": created_at or datetime.now(timezone.utc).isoformat(),
        "question": question,
        "template_id": template_id,
        "status": status,
        "location": normalise_location(location),
        "parameters": parameters or {},
        "results": results or {},
        "sources": source_metadata(
            source_ids,
            registry_path=registry_path,
            lock_path=lock_path,
        ),
        "methods": list(methods),
        "caveats": render_caveats(caveat_ids, path=caveats_path),
        "refusals": render_refusals(refusal_ids, path=refusals_path),
        "query_metadata": metadata,
    }
    return validate_packet(packet, schema_path=schema_path)


def build_refusal_packet(
    *,
    question: str,
    template_id: str,
    refusal_id: str,
    parameters: dict[str, Any] | None = None,
    location: dict[str, Any] | None = None,
    **paths: Any,
) -> dict[str, Any]:
    return build_evidence_packet(
        question=question,
        template_id=template_id,
        status="refused",
        parameters=parameters,
        location=location,
        refusal_ids=[refusal_id],
        methods=["The answer policy mapped this request to an approved refusal."],
        **paths,
    )


def build_error_packet(
    *,
    question: str,
    template_id: str,
    error: str,
    parameters: dict[str, Any] | None = None,
    source_ids: list[str] | tuple[str, ...] = (),
    caveat_ids: list[str] | tuple[str, ...] = (),
    location: dict[str, Any] | None = None,
    **paths: Any,
) -> dict[str, Any]:
    return build_evidence_packet(
        question=question,
        template_id=template_id,
        status="error",
        parameters=parameters,
        results={"error": error},
        source_ids=source_ids,
        caveat_ids=caveat_ids,
        location=location,
        methods=["The deterministic query failed before evidence could be produced."],
        **paths,
    )
