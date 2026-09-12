from pathlib import Path

from trs.ingest.parquet_writer import write_csv_to_parquet, write_manifest_lock, write_source_file_to_parquet
from trs.ingest.registry import SourceFile
from trs.storage.duckdb import create_parquet_views, list_views


def test_create_view_over_generated_parquet(tmp_path: Path) -> None:
    source_path = tmp_path / "sample.csv"
    source_path.write_text("_id,name\n1,A\n2,B\n", encoding="utf-8")
    source_file = SourceFile(
        source_id="sample_source",
        source_name="Sample Source",
        source_status="available_local",
        path=source_path,
        format="csv",
        candidate_primary_keys=("_id",),
    )

    record = write_csv_to_parquet(source_file, processed_dir=tmp_path / "processed", source_file_count=1)
    write_manifest_lock(tmp_path / "manifest.lock.json", [record], [])
    created = create_parquet_views(tmp_path / "trs.duckdb", [record])

    assert created == ["sample_source"]
    assert list_views(tmp_path / "trs.duckdb") == ["sample_source"]
    assert record["row_count"] == 2
    assert record["candidate_primary_keys"]["_id"]["distinct_values"] == 2


def test_write_source_file_to_parquet_supports_xlsx(tmp_path: Path) -> None:
    source_path = tmp_path / "sample.xlsx"
    import pandas as pd

    pd.DataFrame({"_id": ["1"], "name": ["A"]}).to_excel(source_path, index=False)
    source_file = SourceFile(
        source_id="sample_workbook",
        source_name="Sample Workbook",
        source_status="available_local",
        path=source_path,
        format="xlsx",
        candidate_primary_keys=("_id",),
    )

    records, skipped = write_source_file_to_parquet(
        source_file,
        processed_dir=tmp_path / "processed",
        source_file_count=1,
    )

    assert skipped == []
    assert records[0]["view_name"] == "sample_workbook"
    assert records[0]["row_count"] == 1
