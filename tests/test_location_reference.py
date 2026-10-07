from pathlib import Path

import duckdb

from trs.geo.reference import (
    canonical_street_name,
    create_location_reference_tables,
    location_reference_metadata,
)


def test_canonical_street_name_expands_only_trailing_type_and_direction() -> None:
    assert canonical_street_name("King St. W") == "king street west"
    assert canonical_street_name("King Street West") == "king street west"
    assert canonical_street_name("St Clair Ave W") == "st clair avenue west"


def test_reference_tables_use_official_centreline_relationships(tmp_path: Path) -> None:
    db_path = tmp_path / "locations.duckdb"
    with duckdb.connect(str(db_path)) as con:
        con.execute(
            '''create table toronto_intersection_file
               ("INTERSECTION_ID" varchar, "INTERSECTION_DESC" varchar, "geometry" varchar)'''
        )
        con.execute(
            "insert into toronto_intersection_file values ('I1', 'King St W / Spadina Ave', '{\"type\":\"Point\",\"coordinates\":[-79.4,43.6]}')"
        )
        con.execute(
            '''create table toronto_centreline
               ("CENTRELINE_ID" varchar, "LINEAR_NAME_ID" varchar,
                "LINEAR_NAME_FULL" varchar, "LINEAR_NAME" varchar,
                "LINEAR_NAME_TYPE" varchar, "LINEAR_NAME_DIR" varchar,
                "FROM_INTERSECTION_ID" varchar, "TO_INTERSECTION_ID" varchar,
                "geometry" varchar)'''
        )
        con.executemany(
            "insert into toronto_centreline values (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            [
                ("C1", "S1", "King St W", "King", "St", "W", "I1", "I1", "{}"),
                ("C2", "S2", "Spadina Ave", "Spadina", "Ave", None, "I1", "I1", "{}"),
            ],
        )

        created = create_location_reference_tables(con)
        metadata = location_reference_metadata(con)
        aliases = set(con.execute("select alias from location_street_alias").fetchnumpy()["alias"])

    assert created == [
        "location_street",
        "location_street_alias",
        "location_intersection",
        "location_intersection_street",
        "location_reference_metadata",
    ]
    assert metadata == {
        "source_ids": "toronto_centreline+toronto_intersection_file",
        "intersection_count": 1,
        "street_count": 2,
        "relationship_count": 2,
    }
    assert "king street west" in aliases
    assert "spadina avenue" in aliases
