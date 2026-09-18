from pathlib import Path

import duckdb
import pytest

from trs.evidence.catalog import CatalogError
from trs.evidence.engine import EvidenceEngine


def create_fixture_database(path: Path) -> None:
    with duckdb.connect(str(path)) as con:
        con.execute(
            """
            create table ksi_collisions (
                "ACCNUM" varchar,
                "DATE" varchar,
                "TIME" varchar,
                "STREET1" varchar,
                "STREET2" varchar,
                "geometry" varchar,
                "LIGHT" varchar,
                "VISIBILITY" varchar,
                "IMPACTYPE" varchar
            )
            """
        )
        con.executemany(
            "insert into ksi_collisions values (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            [
                ("A", "2021-01-10", "1015", "King St W", "Spadina Ave", "point-a", "Daylight", "Clear", "Turning Movement"),
                ("A", "2021-01-10", "1015", "King St W", "Spadina Ave", "point-a", "Daylight", "Clear", "Turning Movement"),
                ("B", "2021-05-01", "2010", "Queen St W", "Bathurst St", "point-b", "Dark", "Rain", "Rear End"),
                ("C", "2022-07-01", "0900", "Bloor St W", "Dufferin St", "point-c", "Daylight", "Clear", "Angle"),
                ("D", "2019-07-01", "1200", "Danforth Ave", "Pape Ave", "point-d", "Daylight", "Clear", "Angle"),
            ],
        )
        con.execute(
            """
            create table traffic_collisions (
                "_id" varchar,
                "OCC_YEAR" varchar,
                "PEDESTRIAN" varchar,
                "BICYCLE" varchar,
                "MOTORCYCLE" varchar,
                "AUTOMOBILE" varchar
            )
            """
        )
        con.executemany(
            "insert into traffic_collisions values (?, ?, ?, ?, ?, ?)",
            [
                ("1", "2021", "Yes", "No", "No", "Yes"),
                ("2", "2021", "No", "Yes", "No", "Yes"),
                ("3", "2022", "No", "No", "Yes", "No"),
                ("4", "2019", "Yes", "No", "No", "Yes"),
            ],
        )


def test_ksi_trend_counts_distinct_collision_events(tmp_path: Path) -> None:
    db_path = tmp_path / "fixture.duckdb"
    create_fixture_database(db_path)

    packet = EvidenceEngine(db_path).run(
        "ksi_trend",
        question="KSI trend from 2021 through 2022",
        parameters={"start_year": 2021, "end_year": 2022},
        lock_path=tmp_path / "missing.lock.json",
    )

    assert packet["results"]["series"] == [
        {"year": 2021, "ksi_collision_count": 2},
        {"year": 2022, "ksi_collision_count": 1},
    ]
    assert packet["results"]["ksi_collision_count"] == 3
    assert packet["query_metadata"]["data_manifest_version"] is None


def test_ksi_trend_uses_occurrence_fallback_when_accnum_is_missing(tmp_path: Path) -> None:
    db_path = tmp_path / "fixture.duckdb"
    create_fixture_database(db_path)
    with duckdb.connect(str(db_path)) as con:
        con.executemany(
            "insert into ksi_collisions values (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            [
                ("None", "2021-08-20", "0815", "Yonge St", "Eglinton Ave", "point-x", "Daylight", "Clear", "Angle"),
                ("None", "2021-08-20", "0815", "Yonge St", "Eglinton Ave", "point-x", "Daylight", "Clear", "Angle"),
                (None, "2021-09-21", "2210", "Bay St", "College St", "point-y", "Dark", "Rain", "Rear End"),
            ],
        )

    packet = EvidenceEngine(db_path).run(
        "ksi_trend",
        question="KSI trend for 2021",
        parameters={"start_year": 2021, "end_year": 2021},
        lock_path=tmp_path / "missing.lock.json",
    )

    assert packet["results"]["ksi_collision_count"] == 4
    assert "fallback key" in packet["methods"][0]


def test_collision_profile_separates_event_and_ksi_dimensions(tmp_path: Path) -> None:
    db_path = tmp_path / "fixture.duckdb"
    create_fixture_database(db_path)

    packet = EvidenceEngine(db_path).run(
        "collision_profile",
        question="Show the citywide collision profile",
        parameters={"start_year": 2021, "end_year": 2022},
        lock_path=tmp_path / "missing.lock.json",
    )

    assert packet["results"]["collision_count"] == 3
    assert packet["results"]["road_user_collision_counts"] == {
        "pedestrian": 1,
        "bicycle": 1,
        "motorcycle": 1,
        "automobile": 2,
    }
    daylight = next(
        row
        for row in packet["results"]["ksi_condition_breakdown"]
        if row["dimension"] == "light" and row["category"] == "Daylight"
    )
    assert daylight["ksi_collision_count"] == 2


def test_engine_routes_unsupported_intent_to_refusal(tmp_path: Path) -> None:
    packet = EvidenceEngine(tmp_path / "not-needed.duckdb").run(
        "posted_speed_limit_lookup",
        question="What is the posted speed limit?",
        lock_path=tmp_path / "missing.lock.json",
    )

    assert packet["status"] == "refused"
    assert packet["refusals"][0]["refusal_id"] == "posted_speed_limit_source_missing"


def test_engine_refuses_location_template_until_resolver_exists(tmp_path: Path) -> None:
    packet = EvidenceEngine(tmp_path / "not-needed.duckdb").run(
        "intersection_safety_snapshot",
        question="Show an intersection safety snapshot",
        lock_path=tmp_path / "missing.lock.json",
    )

    assert packet["status"] == "refused"
    assert packet["refusals"][0]["refusal_id"] == "location_resolver_unavailable"


def test_engine_rejects_missing_template_parameters(tmp_path: Path) -> None:
    with pytest.raises(CatalogError, match="Missing parameters.*end_year"):
        EvidenceEngine(tmp_path / "not-needed.duckdb").run(
            "ksi_trend",
            question="Show the KSI trend",
            parameters={"start_year": 2021},
        )


def test_engine_rejects_unknown_template_parameters(tmp_path: Path) -> None:
    with pytest.raises(CatalogError, match="Unknown parameters.*unsupported_parameter"):
        EvidenceEngine(tmp_path / "not-needed.duckdb").run(
            "ksi_trend",
            question="Show the KSI trend",
            parameters={"start_year": 2021, "end_year": 2022, "unsupported_parameter": 50},
        )


def test_engine_returns_valid_error_packet_for_query_failure(tmp_path: Path) -> None:
    packet = EvidenceEngine(tmp_path / "missing.duckdb").run(
        "ksi_trend",
        question="Show the KSI trend",
        parameters={"start_year": 2021, "end_year": 2022},
        lock_path=tmp_path / "missing.lock.json",
    )

    assert packet["status"] == "error"
    assert "error" in packet["results"]
    assert packet["sources"][0]["source_id"] == "ksi_collisions"
