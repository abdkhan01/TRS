from __future__ import annotations

from pathlib import Path
from typing import Any

import duckdb

from trs.analysis.templates import (
    collision_profile,
    corridor_snapshot,
    historical_ase_context,
    intersection_snapshot,
    ksi_trend,
    speed_volume_context,
)
from trs.evidence.catalog import CatalogError, load_templates
from trs.evidence.packet import build_error_packet, build_refusal_packet
from trs.geo.resolver import LocationResolutionError, resolve_location


HANDLERS = {
    "ksi_trend": ksi_trend,
    "collision_profile": collision_profile,
    "intersection_safety_snapshot": intersection_snapshot,
    "corridor_safety_snapshot": corridor_snapshot,
    "historical_ase_context": historical_ase_context,
    "speed_volume_context": speed_volume_context,
}


def _validate_parameters(
    template_id: str,
    template: dict[str, Any],
    values: dict[str, Any],
) -> None:
    definitions = template.get("parameters") or {}
    unknown = values.keys() - definitions.keys()
    if unknown:
        names = ", ".join(sorted(unknown))
        raise CatalogError(f"Unknown parameters for '{template_id}': {names}")

    missing = [
        name
        for name, definition in definitions.items()
        if definition.get("required") and name not in values
    ]
    if missing:
        names = ", ".join(sorted(missing))
        raise CatalogError(f"Missing parameters for '{template_id}': {names}")

    for name, value in values.items():
        expected = definitions[name].get("type")
        if expected == "integer" and (not isinstance(value, int) or isinstance(value, bool)):
            raise CatalogError(f"Parameter '{name}' for '{template_id}' must be an integer")


class EvidenceEngine:
    def __init__(self, db_path: Path, *, templates_path: Path | None = None):
        self.db_path = db_path
        self.templates_path = templates_path

    def run(
        self,
        template_id: str,
        *,
        question: str,
        parameters: dict[str, Any] | None = None,
        location: dict[str, Any] | None = None,
        **packet_paths: Any,
    ) -> dict[str, Any]:
        templates = load_templates(self.templates_path)
        if template_id not in templates:
            raise CatalogError(f"Unknown template id: {template_id}")
        template = templates[template_id]
        status = template.get("status")
        if status in {"refused", "deferred"}:
            refusal_id = template.get("refusal_id")
            if not refusal_id:
                raise CatalogError(f"Template '{template_id}' has no refusal id")
            return build_refusal_packet(
                question=question,
                template_id=template_id,
                refusal_id=str(refusal_id),
                parameters=parameters,
                location=location,
                **packet_paths,
            )
        handler_id = str(template.get("handler", ""))
        if handler_id not in HANDLERS:
            raise CatalogError(f"Template '{template_id}' has no implemented handler")
        values = parameters or {}
        source_ids = tuple(str(item) for item in template.get("source_ids", []))
        caveat_ids = tuple(str(item) for item in template.get("caveat_ids", []))
        resolved_location = location
        location_mode = str(template.get("location", "optional"))
        if location is not None:
            if not (location.get("match_confidence") and location.get("geometry")):
                try:
                    resolved_location = resolve_location(self.db_path, location)
                except (LocationResolutionError, duckdb.Error) as exc:
                    return build_refusal_packet(
                        question=question,
                        template_id=template_id,
                        refusal_id="location_resolver_unavailable",
                        parameters=values,
                        location={
                            "input": str(location.get("input", "")),
                            "resolved_name": None,
                            "geometry": None,
                            "match_confidence": "unresolved",
                            "method": f"Local location resolution failed: {exc}",
                        },
                        **packet_paths,
                    )
        elif location_mode == "required":
            return build_refusal_packet(
                question=question,
                template_id=template_id,
                refusal_id="location_resolver_unavailable",
                parameters=values,
                **packet_paths,
            )
        _validate_parameters(template_id, template, values)
        try:
            return HANDLERS[handler_id](
                self.db_path,
                question=question,
                location=resolved_location,
                source_ids=source_ids,
                caveat_ids=caveat_ids,
                **values,
                **packet_paths,
            )
        except (duckdb.Error, ValueError) as exc:
            return build_error_packet(
                question=question,
                template_id=template_id,
                error=str(exc),
                parameters=values,
                source_ids=source_ids,
                caveat_ids=caveat_ids,
                location=resolved_location,
                **packet_paths,
            )
