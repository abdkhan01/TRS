from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

from trs.storage.paths import (
    default_caveats_path,
    default_lock_path,
    default_refusals_path,
    default_registry_path,
    default_templates_path,
)


class CatalogError(ValueError):
    """Raised when evidence configuration is missing or inconsistent."""


def _load_mapping(path: Path, key: str) -> dict[str, dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        payload = yaml.safe_load(handle) or {}
    values = payload.get(key, {})
    if not isinstance(values, dict):
        raise CatalogError(f"{path}: '{key}' must be a mapping")
    return {str(item_id): dict(value or {}) for item_id, value in values.items()}


def load_caveats(path: Path | None = None) -> dict[str, dict[str, Any]]:
    return _load_mapping(path or default_caveats_path(), "caveats")


def load_refusals(path: Path | None = None) -> dict[str, dict[str, Any]]:
    return _load_mapping(path or default_refusals_path(), "refusals")


def load_templates(path: Path | None = None) -> dict[str, dict[str, Any]]:
    template_path = path or default_templates_path()
    with template_path.open("r", encoding="utf-8") as handle:
        payload = yaml.safe_load(handle) or {}
    items = payload.get("templates", [])
    if not isinstance(items, list):
        raise CatalogError(f"{template_path}: 'templates' must be a list")

    templates: dict[str, dict[str, Any]] = {}
    for item in items:
        if not isinstance(item, dict) or "id" not in item:
            raise CatalogError(f"{template_path}: every template must have an id")
        template_id = str(item["id"])
        if template_id in templates:
            raise CatalogError(f"{template_path}: duplicate template id '{template_id}'")
        templates[template_id] = dict(item)
    return templates


def render_caveats(
    caveat_ids: list[str] | tuple[str, ...],
    *,
    path: Path | None = None,
) -> list[dict[str, str]]:
    catalog = load_caveats(path)
    rendered = []
    for caveat_id in caveat_ids:
        try:
            text = catalog[caveat_id]["text"]
        except KeyError as exc:
            raise CatalogError(f"Unknown caveat id: {caveat_id}") from exc
        rendered.append({"caveat_id": caveat_id, "text": str(text)})
    return rendered


def render_refusals(
    refusal_ids: list[str] | tuple[str, ...],
    *,
    path: Path | None = None,
) -> list[dict[str, str | None]]:
    catalog = load_refusals(path)
    rendered = []
    for refusal_id in refusal_ids:
        try:
            refusal = catalog[refusal_id]
            reason = refusal["reason"]
        except KeyError as exc:
            raise CatalogError(f"Unknown refusal id: {refusal_id}") from exc
        rendered.append(
            {
                "refusal_id": refusal_id,
                "reason": str(reason),
                "allowed_alternative": refusal.get("allowed_alternative"),
            }
        )
    return rendered


def _load_source_registry(path: Path) -> dict[str, dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        payload = yaml.safe_load(handle) or {}
    return {str(item["id"]): dict(item) for item in payload.get("sources", [])}


def _load_manifest(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def manifest_version(path: Path | None = None) -> str | None:
    return _load_manifest(path or default_lock_path()).get("generated_at")


def source_metadata(
    source_ids: list[str] | tuple[str, ...],
    *,
    registry_path: Path | None = None,
    lock_path: Path | None = None,
) -> list[dict[str, Any]]:
    registry = _load_source_registry(registry_path or default_registry_path())
    manifest = _load_manifest(lock_path or default_lock_path())
    records_by_source: dict[str, list[dict[str, Any]]] = {}
    for record in manifest.get("records", []):
        records_by_source.setdefault(str(record.get("source_id")), []).append(record)

    sources = []
    for source_id in source_ids:
        if source_id not in registry:
            raise CatalogError(f"Unknown source id: {source_id}")
        source = registry[source_id]
        if source.get("query_eligible", True) is False:
            raise CatalogError(f"Source is not eligible for evidence queries: {source_id}")
        records = records_by_source.get(source_id, [])
        hashes = sorted(
            str(record["input_sha256"])
            for record in records
            if record.get("input_sha256")
        )
        generated = sorted(
            str(record["generated_at"])
            for record in records
            if record.get("generated_at")
        )
        local_paths = source.get("local_paths") or []
        sources.append(
            {
                "source_id": source_id,
                "source_name": str(source.get("name", source_id)),
                "status": str(source.get("status", "unknown")),
                "version": ",".join(hashes) or None,
                "source_url": source.get("source_url"),
                "local_path": str(local_paths[0]) if local_paths else None,
                "date_range": str(source["date_range"]) if source.get("date_range") is not None else None,
                "downloaded_at": generated[-1] if generated else None,
            }
        )
    return sources
