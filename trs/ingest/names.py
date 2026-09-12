from __future__ import annotations

import re
from pathlib import Path


KNOWN_VIEW_NAMES = {
    ("traffic_collisions", "4ad77de0-a9e0-4725-95d9-dbce6776d6cf"): "traffic_collisions",
    ("ksi_collisions", "c9b88f1f-863e-42f1-ada0-2c09b1e2eaa4"): "ksi_collisions",
    ("traffic_volume", "svc_most_recent_summary_data"): "traffic_volume_summary",
    ("traffic_volume", "svc_raw_data_volume_2015_2019"): "traffic_volume_raw_2015_2019",
    ("traffic_volume", "svc_raw_data_volume_2020_2024"): "traffic_volume_raw_2020_2024",
    ("automated_speed_enforcement_locations", "e25e9460-a0e8-469c-b9fb-9a4837ac6c1c"): "automated_speed_enforcement_locations",
}


def slug(value: str) -> str:
    cleaned = re.sub(r"[^0-9a-zA-Z]+", "_", value).strip("_").lower()
    return re.sub(r"_+", "_", cleaned)


def dataset_stem(path: Path | str) -> str:
    return slug(Path(path).stem)


def view_name_for(source_id: str, path: Path, source_file_count: int) -> str:
    known = KNOWN_VIEW_NAMES.get((source_id, path.stem))
    if known:
        return known
    if source_file_count == 1:
        return slug(source_id)
    return slug(f"{source_id}_{path.stem}")
