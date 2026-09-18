import json
from pathlib import Path

import duckdb

from trs.evidence.engine import EvidenceEngine
from trs.geo.resolver import LocationResolver, resolve_location


def geojson(geometry_type: str, coordinates) -> str:
    return json.dumps({"type": geometry_type, "coordinates": coordinates})


def create_geospatial_fixture(path: Path) -> None:
    with duckdb.connect(str(path)) as con:
        con.execute(
            '''create table toronto_intersection_file
               ("INTERSECTION_ID" varchar, "INTERSECTION_DESC" varchar, "geometry" varchar)'''
        )
        con.executemany(
            "insert into toronto_intersection_file values (?, ?, ?)",
            [
                ("I1", "Alpha St / Beta Ave", geojson("MultiPoint", [[-79.4000, 43.7000]])),
                ("I2", "Alpha St / Gamma Rd", geojson("MultiPoint", [[-79.3900, 43.7000]])),
            ],
        )
        con.execute(
            '''create table toronto_centreline
               ("CENTRELINE_ID" varchar, "LINEAR_NAME_FULL" varchar,
                "FROM_INTERSECTION_ID" varchar, "TO_INTERSECTION_ID" varchar, "geometry" varchar)'''
        )
        con.execute(
            "insert into toronto_centreline values (?, ?, ?, ?, ?)",
            ["C1", "Alpha St", "I1", "I2", geojson("MultiLineString", [[[-79.4000, 43.7000], [-79.3900, 43.7000]]])],
        )
        con.execute(
            '''create table traffic_collisions
               ("_id" varchar, "OCC_YEAR" varchar, "PEDESTRIAN" varchar,
                "BICYCLE" varchar, "MOTORCYCLE" varchar, "AUTOMOBILE" varchar,
                "geometry" varchar)'''
        )
        con.executemany(
            "insert into traffic_collisions values (?, ?, ?, ?, ?, ?, ?)",
            [
                ("T1", "2022", "YES", "NO", "NO", "YES", geojson("Point", [-79.4001, 43.7000])),
                ("T2", "2022", "NO", "YES", "NO", "YES", geojson("Point", [-79.3950, 43.7001])),
                ("T3", "2022", "NO", "NO", "YES", "NO", geojson("Point", [-79.4500, 43.7500])),
            ],
        )
        con.execute(
            '''create table ksi_collisions
               ("ACCNUM" varchar, "DATE" varchar, "TIME" varchar, "LIGHT" varchar,
                "VISIBILITY" varchar, "IMPACTYPE" varchar, "ACCLASS" varchar,
                "RDSFCOND" varchar, "geometry" varchar)'''
        )
        con.executemany(
            "insert into ksi_collisions values (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            [
                ("K1", "2022-02-01", "830", "Daylight", "Clear", "Angle", "Fatal", "Dry", geojson("Point", [-79.4001, 43.7000])),
                ("K1", "2022-02-01", "830", "Daylight", "Clear", "Angle", "Fatal", "Dry", geojson("Point", [-79.4001, 43.7000])),
                ("K2", "2022-03-01", "1900", "Dark", "Rain", "Rear End", "Injury", "Wet", geojson("Point", [-79.3950, 43.7001])),
                ("K3", "2022-04-01", "1200", "Daylight", "Clear", "Angle", "Injury", "Dry", geojson("Point", [-79.4500, 43.7500])),
            ],
        )
        con.execute(
            '''create table automated_speed_enforcement_locations
               ("FID" varchar, "location" varchar, "Status" varchar, "geometry" varchar)'''
        )
        con.executemany(
            "insert into automated_speed_enforcement_locations values (?, ?, ?, ?)",
            [
                ("A1", "Alpha at Beta", "Historical", geojson("Point", [-79.4002, 43.7000])),
                ("A2", "Far away", "Historical", geojson("Point", [-79.5000, 43.8000])),
            ],
        )
        con.execute(
            '''create table traffic_volume_summary
               ("latest_count_id" varchar, "latest_count_type" varchar,
                "latest_count_date_start" varchar, "latest_count_date_end" varchar,
                "location_name" varchar, "longitude" varchar, "latitude" varchar,
                "avg_daily_vol" varchar, "avg_weekday_daily_vol" varchar,
                "avg_weekend_daily_vol" varchar, "avg_speed" varchar,
                "avg_85th_percentile_speed" varchar, "avg_95th_percentile_speed" varchar)'''
        )
        con.executemany(
            "insert into traffic_volume_summary values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            [
                ("V1", "ATR", "2024-01-01", "2024-01-03", "Alpha", "-79.4002", "43.7000", "1000", "1100", "900", "32", "40", "45"),
                ("V2", "ATR", "2024-01-01", "2024-01-03", "Far", "-79.5000", "43.8000", "2000", "2100", "1900", "42", "50", "55"),
            ],
        )


def test_named_intersection_resolver_and_snapshot(tmp_path: Path) -> None:
    db_path = tmp_path / "geo.duckdb"
    create_geospatial_fixture(db_path)
    resolver = LocationResolver(db_path)
    location = resolver.resolve("Alpha St and Beta Ave")

    assert location["resolved_name"] == "Alpha St / Beta Ave"
    assert location["match_confidence"] == "high"
    assert location["crs"] == "EPSG:4326"
    packet = EvidenceEngine(db_path).run(
        "intersection_safety_snapshot",
        question="Snapshot",
        parameters={"start_year": 2022, "end_year": 2022, "buffer_meters": 50},
        location=location,
        lock_path=tmp_path / "missing.lock.json",
    )
    assert packet["status"] == "answered"
    assert packet["results"]["collision_count"] == 1
    assert packet["results"]["ksi_collision_count"] == 1
    assert packet["location"] == location
    assert {source["source_id"] for source in packet["sources"]} == {
        "traffic_collisions",
        "ksi_collisions",
        "toronto_intersection_file",
    }


def test_location_scoped_trend_profile_and_context(tmp_path: Path) -> None:
    db_path = tmp_path / "geo.duckdb"
    create_geospatial_fixture(db_path)
    location = {"input": "manual", "latitude": 43.7000, "longitude": -79.4000}
    engine = EvidenceEngine(db_path)

    trend = engine.run(
        "ksi_trend",
        question="Trend",
        parameters={"start_year": 2022, "end_year": 2022, "buffer_meters": 50},
        location=location,
        lock_path=tmp_path / "missing.lock.json",
    )
    profile = engine.run(
        "collision_profile",
        question="Profile",
        parameters={"start_year": 2022, "end_year": 2022, "buffer_meters": 50},
        location=location,
        lock_path=tmp_path / "missing.lock.json",
    )
    ase = engine.run(
        "historical_ase_context",
        question="ASE",
        parameters={"buffer_meters": 100},
        location=location,
        lock_path=tmp_path / "missing.lock.json",
    )
    volume = engine.run(
        "speed_volume_context",
        question="Volume",
        parameters={"buffer_meters": 100, "limit": 10},
        location=location,
        lock_path=tmp_path / "missing.lock.json",
    )

    assert trend["results"]["ksi_collision_count"] == 1
    assert profile["results"]["collision_count"] == 1
    assert {row["dimension"] for row in profile["results"]["ksi_condition_breakdown"]} >= {
        "severity", "time_period", "light", "visibility", "road_condition", "impact_type"
    }
    assert ase["results"]["camera_location_count"] == 1
    assert volume["results"]["observation_count"] == 1
    assert volume["results"]["observations"][0]["average_observed_speed"] == 32.0


def test_centreline_corridor_filters_to_route(tmp_path: Path) -> None:
    db_path = tmp_path / "geo.duckdb"
    create_geospatial_fixture(db_path)
    corridor = resolve_location(
        db_path,
        {
            "type": "corridor",
            "input": "Alpha corridor",
            "street_name": "Alpha St",
            "start": {"input": "Alpha St and Beta Ave"},
            "end": {"input": "Alpha St and Gamma Rd"},
        },
    )
    assert corridor["match_confidence"] == "high"
    assert corridor["centreline_ids"] == ["C1"]
    assert corridor["geometry"]["type"] == "MultiLineString"

    packet = EvidenceEngine(db_path).run(
        "corridor_safety_snapshot",
        question="Corridor snapshot",
        parameters={"start_year": 2022, "end_year": 2022, "buffer_meters": 30},
        location=corridor,
        lock_path=tmp_path / "missing.lock.json",
    )
    assert packet["status"] == "answered"
    assert packet["results"]["collision_count"] == 2
    assert packet["results"]["ksi_collision_count"] == 2
    assert "toronto_centreline" in {source["source_id"] for source in packet["sources"]}


def test_unmatched_location_returns_approved_refusal(tmp_path: Path) -> None:
    db_path = tmp_path / "geo.duckdb"
    create_geospatial_fixture(db_path)
    packet = EvidenceEngine(db_path).run(
        "intersection_safety_snapshot",
        question="Unknown",
        parameters={"start_year": 2022, "end_year": 2022},
        location={"input": "Missing Rd and Nowhere Ave"},
        lock_path=tmp_path / "missing.lock.json",
    )
    assert packet["status"] == "refused"
    assert packet["location"]["match_confidence"] == "unresolved"
    assert packet["refusals"][0]["refusal_id"] == "location_resolver_unavailable"
