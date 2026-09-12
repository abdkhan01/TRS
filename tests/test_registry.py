from pathlib import Path

from trs.ingest.registry import iter_source_files, load_sources


def test_load_sources(tmp_path: Path) -> None:
    registry = tmp_path / "data_sources.yaml"
    registry.write_text(
        """
sources:
  - id: sample
    name: Sample
    status: available_local
    local_paths:
      - datasets/sample.csv
""",
        encoding="utf-8",
    )

    sources = load_sources(registry)

    assert [source.id for source in sources] == ["sample"]
    assert sources[0].is_local


def test_iter_source_files_resolves_relative_paths(tmp_path: Path) -> None:
    registry = tmp_path / "data_sources.yaml"
    registry.write_text(
        """
sources:
  - id: sample
    name: Sample
    status: available_local
    local_paths:
      - datasets/sample.csv
""",
        encoding="utf-8",
    )

    files = iter_source_files(registry, root=tmp_path)

    assert files[0].path == tmp_path / "datasets" / "sample.csv"
    assert files[0].ingestible
