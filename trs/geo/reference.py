from __future__ import annotations

import re
from typing import Any

import duckdb


_TOKEN = re.compile(r"[^a-z0-9]+")
_ROAD_TYPES = {
    "av": "avenue",
    "ave": "avenue",
    "avenue": "avenue",
    "blvd": "boulevard",
    "boulevard": "boulevard",
    "cir": "circle",
    "circle": "circle",
    "ct": "court",
    "crt": "court",
    "court": "court",
    "cres": "crescent",
    "crescent": "crescent",
    "dr": "drive",
    "drive": "drive",
    "gdns": "gardens",
    "gardens": "gardens",
    "grv": "grove",
    "grove": "grove",
    "hwy": "highway",
    "highway": "highway",
    "ln": "lane",
    "lane": "lane",
    "pkwy": "parkway",
    "parkway": "parkway",
    "pl": "place",
    "place": "place",
    "rd": "road",
    "road": "road",
    "sq": "square",
    "square": "square",
    "st": "street",
    "street": "street",
    "ter": "terrace",
    "terrace": "terrace",
    "trl": "trail",
    "trail": "trail",
}
_DIRECTIONS = {
    "e": "east",
    "east": "east",
    "n": "north",
    "ne": "northeast",
    "north": "north",
    "northeast": "northeast",
    "northwest": "northwest",
    "nw": "northwest",
    "s": "south",
    "se": "southeast",
    "south": "south",
    "southeast": "southeast",
    "southwest": "southwest",
    "sw": "southwest",
    "w": "west",
    "west": "west",
}


def canonical_street_name(value: str) -> str:
    """Return a deterministic Toronto-oriented street search key.

    Only a trailing road type and direction are expanded. This deliberately
    avoids treating the leading ``St`` in names such as ``St Clair`` as the
    road type ``Street``.
    """

    tokens = [token for token in _TOKEN.sub(" ", value.lower()).split() if token]
    if not tokens:
        return ""
    if tokens[-1] in _DIRECTIONS:
        tokens[-1] = _DIRECTIONS[tokens[-1]]
        road_type_index = len(tokens) - 2
    else:
        road_type_index = len(tokens) - 1
    if road_type_index >= 0 and tokens[road_type_index] in _ROAD_TYPES:
        tokens[road_type_index] = _ROAD_TYPES[tokens[road_type_index]]
    return " ".join(tokens)


def _aliases(
    official_name: str,
    base_name: str | None,
) -> set[tuple[str, str]]:
    values = {(canonical_street_name(official_name), "official")}
    if base_name and base_name.lower() != "none":
        values.add((canonical_street_name(base_name), "base"))
    normalized = canonical_street_name(official_name)
    if normalized.startswith("st "):
        values.add(("saint " + normalized[3:], "saint_variant"))
    elif normalized.startswith("saint "):
        values.add(("st " + normalized[6:], "saint_variant"))
    return {(alias, alias_type) for alias, alias_type in values if alias}


def location_reference_sources_available(con: duckdb.DuckDBPyConnection) -> bool:
    rows = con.execute(
        """
        select table_name
        from information_schema.tables
        where table_schema = 'main'
          and table_name in ('toronto_centreline', 'toronto_intersection_file')
        """
    ).fetchall()
    return {str(row[0]) for row in rows} == {
        "toronto_centreline",
        "toronto_intersection_file",
    }


def create_location_reference_tables(con: duckdb.DuckDBPyConnection) -> list[str]:
    """Materialize canonical local location entities from official Toronto IDs."""

    if not location_reference_sources_available(con):
        return []

    con.execute(
        """
        create or replace table location_street as
        select
            cast("LINEAR_NAME_ID" as varchar) as street_id,
            min(cast("LINEAR_NAME_FULL" as varchar)) as official_name,
            min(cast("LINEAR_NAME" as varchar)) as base_name,
            min(cast("LINEAR_NAME_TYPE" as varchar)) as road_type,
            min(cast("LINEAR_NAME_DIR" as varchar)) as direction
        from toronto_centreline
        where "LINEAR_NAME_ID" is not null and "LINEAR_NAME_FULL" is not null
        group by "LINEAR_NAME_ID"
        """
    )
    street_rows = con.execute(
        "select street_id, official_name, base_name from location_street order by street_id"
    ).fetchall()
    alias_rows: list[tuple[str, str, str]] = []
    canonical_rows: list[tuple[str, str]] = []
    for street_id, official_name, base_name in street_rows:
        canonical = canonical_street_name(str(official_name))
        canonical_rows.append((canonical, str(street_id)))
        alias_rows.extend(
            (str(street_id), alias, alias_type)
            for alias, alias_type in _aliases(str(official_name), None if base_name is None else str(base_name))
        )

    con.execute("alter table location_street add column canonical_name varchar")
    con.executemany(
        "update location_street set canonical_name = ? where street_id = ?",
        canonical_rows,
    )
    con.execute(
        """
        create or replace table location_street_alias (
            street_id varchar not null,
            alias varchar not null,
            alias_type varchar not null
        )
        """
    )
    if alias_rows:
        con.executemany(
            "insert into location_street_alias values (?, ?, ?)",
            sorted(set(alias_rows)),
        )

    con.execute(
        """
        create or replace table location_intersection as
        select
            cast("INTERSECTION_ID" as varchar) as intersection_id,
            cast("INTERSECTION_DESC" as varchar) as official_description,
            cast("geometry" as varchar) as geometry
        from toronto_intersection_file
        where "INTERSECTION_ID" is not null and "geometry" is not null
        qualify row_number() over (
            partition by "INTERSECTION_ID" order by "INTERSECTION_ID"
        ) = 1
        """
    )
    con.execute(
        """
        create or replace table location_intersection_street as
        select distinct cast(intersection_id as varchar) as intersection_id,
                        cast("LINEAR_NAME_ID" as varchar) as street_id
        from (
            select "FROM_INTERSECTION_ID" as intersection_id, "LINEAR_NAME_ID"
            from toronto_centreline
            union all
            select "TO_INTERSECTION_ID" as intersection_id, "LINEAR_NAME_ID"
            from toronto_centreline
        )
        where intersection_id is not null and "LINEAR_NAME_ID" is not null
        """
    )
    con.execute(
        """
        create or replace table location_reference_metadata as
        select
            'toronto_centreline+toronto_intersection_file'::varchar as source_ids,
            count(*)::bigint as intersection_count,
            (select count(*) from location_street)::bigint as street_count,
            (select count(*) from location_intersection_street)::bigint as relationship_count
        from location_intersection
        """
    )
    return [
        "location_street",
        "location_street_alias",
        "location_intersection",
        "location_intersection_street",
        "location_reference_metadata",
    ]


def location_reference_metadata(con: duckdb.DuckDBPyConnection) -> dict[str, Any] | None:
    try:
        row = con.execute("select * from location_reference_metadata").fetchone()
    except duckdb.Error:
        return None
    if row is None:
        return None
    columns = [item[0] for item in con.description]
    return dict(zip(columns, row, strict=True))
