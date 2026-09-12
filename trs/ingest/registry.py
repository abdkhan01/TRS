from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


LOCAL_STATUSES = {"available_local", "registered_local"}
INGESTIBLE_SUFFIXES = {".csv", ".xlsx", ".xls", ".zip"}
SKIPPED_SUFFIXES = {".geojson", ".json", ".gpkg", ".pdf", ".docx"}


@dataclass(frozen=True)
class SourceFile:
    source_id: str
    source_name: str
    source_status: str
    path: Path
    format: str
    grain: str | None = None
    geometry: str | None = None
    date_fields: tuple[str, ...] = ()
    candidate_primary_keys: tuple[str, ...] = ()
    candidate_event_keys: tuple[str, ...] = ()
    caveat_ids: tuple[str, ...] = ()

    @property
    def exists(self) -> bool:
        return self.path.exists()

    @property
    def ingestible(self) -> bool:
        return self.path.suffix.lower() in INGESTIBLE_SUFFIXES

    @property
    def skipped_reason(self) -> str | None:
        suffix = self.path.suffix.lower()
        if suffix in INGESTIBLE_SUFFIXES:
            return None
        if suffix in SKIPPED_SUFFIXES:
            return f"{suffix[1:]} ingestion is not part of the current tabular ingestion pass"
        return f"unsupported file suffix: {suffix or '<none>'}"


@dataclass(frozen=True)
class Source:
    id: str
    name: str
    status: str
    raw: dict[str, Any] = field(repr=False)

    @property
    def local_paths(self) -> tuple[str, ...]:
        paths = self.raw.get("local_paths") or []
        return tuple(str(path) for path in paths)

    @property
    def is_local(self) -> bool:
        return self.status in LOCAL_STATUSES


def load_sources(registry_path: Path) -> list[Source]:
    with registry_path.open("r", encoding="utf-8") as handle:
        payload = yaml.safe_load(handle) or {}

    sources = []
    for item in payload.get("sources", []):
        sources.append(
            Source(
                id=str(item["id"]),
                name=str(item.get("name", item["id"])),
                status=str(item.get("status", "unknown")),
                raw=item,
            )
        )
    return sources


def iter_source_files(
    registry_path: Path,
    *,
    root: Path,
    include_sources: set[str] | None = None,
    local_only: bool = True,
) -> list[SourceFile]:
    files: list[SourceFile] = []
    for source in load_sources(registry_path):
        if include_sources and source.id not in include_sources:
            continue
        if local_only and not source.is_local:
            continue
        for raw_path in source.local_paths:
            path = Path(raw_path)
            if not path.is_absolute():
                path = root / path
            files.append(
                SourceFile(
                    source_id=source.id,
                    source_name=source.name,
                    source_status=source.status,
                    path=path,
                    format=path.suffix.lower().lstrip("."),
                    grain=source.raw.get("grain"),
                    geometry=source.raw.get("geometry"),
                    date_fields=tuple(source.raw.get("date_fields") or []),
                    candidate_primary_keys=tuple(source.raw.get("candidate_primary_keys") or []),
                    candidate_event_keys=tuple(source.raw.get("candidate_event_keys") or []),
                    caveat_ids=tuple(source.raw.get("caveat_ids") or []),
                )
            )
    return files
