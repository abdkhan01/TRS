from __future__ import annotations

import hashlib
import json
import tempfile
import zipfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import duckdb
import pandas as pd

from trs.ingest.names import dataset_stem, view_name_for
from trs.ingest.registry import SourceFile


def _sql_string(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def _file_sha256(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()


def _inspect_parquet(con: duckdb.DuckDBPyConnection, parquet_path: Path) -> dict[str, Any]:
    parquet_sql = _sql_string(str(parquet_path))
    row_count = con.execute(f"select count(*) from read_parquet({parquet_sql})").fetchone()[0]
    description = con.execute(f"describe select * from read_parquet({parquet_sql})").fetchall()
    columns = [{"name": row[0], "type": row[1], "nullable": row[2]} for row in description]
    return {"row_count": row_count, "columns": columns}


def _profile_record(
    *,
    con: duckdb.DuckDBPyConnection,
    source_file: SourceFile,
    output_path: Path,
    view_name: str,
    input_sha256: str,
    input_size_bytes: int,
    input_member: str | None = None,
    input_sheet: str | None = None,
) -> dict[str, Any]:
    profile = _inspect_parquet(con, output_path)
    output_sql = _sql_string(str(output_path))
    column_names = {column["name"] for column in profile["columns"]}
    primary_keys = {}
    for key in source_file.candidate_primary_keys:
        if key in column_names:
            result = con.execute(
                f"""
                select count(*) as rows, count(distinct "{key}") as distinct_values
                from read_parquet({output_sql})
                """
            ).fetchone()
            primary_keys[key] = {"rows": result[0], "distinct_values": result[1]}

    event_keys = {}
    for key in source_file.candidate_event_keys:
        if key in column_names:
            result = con.execute(
                f"""
                select count(*) as rows, count(distinct "{key}") as distinct_values
                from read_parquet({output_sql})
                """
            ).fetchone()
            event_keys[key] = {"rows": result[0], "distinct_values": result[1]}

    record = {
        "source_id": source_file.source_id,
        "source_name": source_file.source_name,
        "source_status": source_file.source_status,
        "view_name": view_name,
        "input_path": str(source_file.path),
        "input_sha256": input_sha256,
        "input_size_bytes": input_size_bytes,
        "input_format": source_file.format,
        "output_path": str(output_path),
        "output_format": "parquet",
        "generated_at": datetime.now(UTC).isoformat(),
        "grain": source_file.grain,
        "geometry": source_file.geometry,
        "date_fields": {
            "registered": list(source_file.date_fields),
            "present": [field for field in source_file.date_fields if field in column_names],
            "missing": [field for field in source_file.date_fields if field not in column_names],
        },
        "candidate_primary_keys": primary_keys,
        "candidate_event_keys": event_keys,
        "caveat_ids": list(source_file.caveat_ids),
        **profile,
    }
    if input_member:
        record["input_member"] = input_member
    if input_sheet:
        record["input_sheet"] = input_sheet
    return record


def write_csv_to_parquet(
    source_file: SourceFile,
    *,
    processed_dir: Path,
    source_file_count: int,
    overwrite: bool = True,
    view_name: str | None = None,
    input_path: Path | None = None,
    input_member: str | None = None,
    input_sha256: str | None = None,
    input_size_bytes: int | None = None,
) -> dict[str, Any]:
    input_path = input_path or source_file.path
    output_dir = processed_dir / source_file.source_id
    output_dir.mkdir(parents=True, exist_ok=True)

    stem = view_name or view_name_for(source_file.source_id, source_file.path, source_file_count)
    output_path = output_dir / f"{stem}.parquet"
    if output_path.exists() and not overwrite:
        raise FileExistsError(f"{output_path} already exists")

    con = duckdb.connect(database=":memory:")
    source_sql = _sql_string(str(input_path))
    output_sql = _sql_string(str(output_path))
    con.execute(
        f"""
        copy (
            select *
            from read_csv(
                {source_sql},
                header = true,
                delim = ',',
                quote = '"',
                escape = '"',
                union_by_name = true,
                all_varchar = true,
                ignore_errors = true,
                strict_mode = false,
                null_padding = true,
                parallel = false
            )
        )
        to {output_sql}
        (format parquet, compression zstd)
        """
    )
    return _profile_record(
        con=con,
        source_file=source_file,
        output_path=output_path,
        view_name=stem,
        input_sha256=input_sha256 or _file_sha256(source_file.path),
        input_size_bytes=input_size_bytes if input_size_bytes is not None else source_file.path.stat().st_size,
        input_member=input_member,
    )


def write_xlsx_to_parquet(
    source_file: SourceFile,
    *,
    processed_dir: Path,
    source_file_count: int,
    overwrite: bool = True,
) -> list[dict[str, Any]]:
    output_dir = processed_dir / source_file.source_id
    output_dir.mkdir(parents=True, exist_ok=True)
    workbook = pd.ExcelFile(source_file.path)
    records = []
    input_sha256 = _file_sha256(source_file.path)
    input_size_bytes = source_file.path.stat().st_size

    for sheet_name in workbook.sheet_names:
        if len(workbook.sheet_names) == 1 and source_file_count == 1:
            view_name = view_name_for(source_file.source_id, source_file.path, source_file_count)
        else:
            view_name = f"{view_name_for(source_file.source_id, source_file.path, source_file_count)}_{dataset_stem(Path(sheet_name))}"
        output_path = output_dir / f"{view_name}.parquet"
        if output_path.exists() and not overwrite:
            raise FileExistsError(f"{output_path} already exists")
        frame = workbook.parse(sheet_name=sheet_name, dtype=str)
        frame.to_parquet(output_path, engine="pyarrow", compression="zstd", index=False)
        con = duckdb.connect(database=":memory:")
        records.append(
            _profile_record(
                con=con,
                source_file=source_file,
                output_path=output_path,
                view_name=view_name,
                input_sha256=input_sha256,
                input_size_bytes=input_size_bytes,
                input_sheet=sheet_name,
            )
        )
    return records


def write_zip_csvs_to_parquet(
    source_file: SourceFile,
    *,
    processed_dir: Path,
    overwrite: bool = True,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    records = []
    skipped = []
    input_sha256 = _file_sha256(source_file.path)
    input_size_bytes = source_file.path.stat().st_size

    with zipfile.ZipFile(source_file.path) as archive:
        members = [member for member in archive.infolist() if not member.is_dir()]
        csv_members = [member for member in members if Path(member.filename).suffix.lower() == ".csv"]
        for member in members:
            if Path(member.filename).suffix.lower() != ".csv":
                skipped.append(
                    {
                        "source_id": source_file.source_id,
                        "input_path": str(source_file.path),
                        "input_member": member.filename,
                        "reason": "non-csv ZIP member skipped",
                    }
                )
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            for member in csv_members:
                extracted_path = tmpdir_path / Path(member.filename).name
                with archive.open(member) as source, extracted_path.open("wb") as target:
                    target.write(source.read())
                view_name = f"{dataset_stem(Path(source_file.source_id))}_{dataset_stem(Path(member.filename).stem)}"
                records.append(
                    write_csv_to_parquet(
                        source_file,
                        processed_dir=processed_dir,
                        source_file_count=len(csv_members),
                        overwrite=overwrite,
                        view_name=view_name,
                        input_path=extracted_path,
                        input_member=member.filename,
                        input_sha256=input_sha256,
                        input_size_bytes=input_size_bytes,
                    )
                )
    return records, skipped


def write_source_file_to_parquet(
    source_file: SourceFile,
    *,
    processed_dir: Path,
    source_file_count: int,
    overwrite: bool = True,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    suffix = source_file.path.suffix.lower()
    if suffix == ".csv":
        return [
            write_csv_to_parquet(
                source_file,
                processed_dir=processed_dir,
                source_file_count=source_file_count,
                overwrite=overwrite,
            )
        ], []
    if suffix in {".xlsx", ".xls"}:
        return write_xlsx_to_parquet(
            source_file,
            processed_dir=processed_dir,
            source_file_count=source_file_count,
            overwrite=overwrite,
        ), []
    if suffix == ".zip":
        return write_zip_csvs_to_parquet(
            source_file,
            processed_dir=processed_dir,
            overwrite=overwrite,
        )
    raise ValueError(f"Unsupported ingestible file type: {suffix}")


def write_manifest_lock(lock_path: Path, records: list[dict[str, Any]], skipped: list[dict[str, Any]]) -> None:
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "generated_at": datetime.now(UTC).isoformat(),
        "records": records,
        "skipped": skipped,
    }
    lock_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def read_manifest_lock(lock_path: Path) -> dict[str, Any]:
    return json.loads(lock_path.read_text(encoding="utf-8"))
