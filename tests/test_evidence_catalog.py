from pathlib import Path

import pytest

from trs.evidence.catalog import CatalogError, load_templates, render_caveats, render_refusals, source_metadata


def test_catalogs_render_packet_objects() -> None:
    caveats = render_caveats(["ksi_party_grain"])
    refusals = render_refusals(["recommendation_not_supported"])

    assert caveats[0]["caveat_id"] == "ksi_party_grain"
    assert "collision identifier" in caveats[0]["text"]
    assert refusals[0]["refusal_id"] == "recommendation_not_supported"
    assert refusals[0]["allowed_alternative"]


def test_template_catalog_contains_implemented_and_refused_behaviors() -> None:
    templates = load_templates()

    assert templates["ksi_trend"]["status"] == "implemented"
    assert templates["posted_speed_limit_lookup"]["status"] == "refused"


def test_source_metadata_merges_manifest_provenance(tmp_path: Path) -> None:
    lock_path = tmp_path / "manifest.lock.json"
    lock_path.write_text(
        """
{
  "generated_at": "2026-01-02T00:00:00+00:00",
  "records": [
    {
      "source_id": "ksi_collisions",
      "input_sha256": "abc123",
      "generated_at": "2026-01-01T00:00:00+00:00"
    }
  ]
}
""",
        encoding="utf-8",
    )

    sources = source_metadata(["ksi_collisions"], lock_path=lock_path)

    assert sources[0]["version"] == "abc123"
    assert sources[0]["downloaded_at"] == "2026-01-01T00:00:00+00:00"


def test_incorrect_ontario_road_network_is_not_query_eligible() -> None:
    with pytest.raises(CatalogError, match="not eligible"):
        source_metadata(["ontario_road_network_road_net_element"])
