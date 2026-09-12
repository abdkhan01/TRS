from __future__ import annotations

from pathlib import Path


def project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def default_registry_path(root: Path | None = None) -> Path:
    return (root or project_root()) / "config" / "data_sources.yaml"


def default_processed_dir(root: Path | None = None) -> Path:
    return (root or project_root()) / "data" / "processed"


def default_duckdb_path(root: Path | None = None) -> Path:
    return (root or project_root()) / "data" / "trs.duckdb"


def default_lock_path(root: Path | None = None) -> Path:
    return (root or project_root()) / "data" / "manifest.lock.json"
