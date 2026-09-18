from pathlib import Path

from streamlit.testing.v1 import AppTest


def _response() -> dict:
    return {
        "status": "answered",
        "summary": "A deterministic fixture summary.",
        "metrics": {"total_runtime_ms": 12.0},
        "packet": {
            "packet_id": "packet-1",
            "created_at": "2026-09-18T00:00:00+00:00",
            "question": "Fixture question",
            "template_id": "intersection_safety_snapshot",
            "status": "answered",
            "location": {
                "input": "King St W and Spadina Ave",
                "resolved_name": "Spadina Ave / King St W",
                "match_confidence": "high",
                "method": "Fixture resolver",
            },
            "parameters": {"start_year": 2019, "end_year": 2023},
            "results": {"collision_count": 12, "ksi_collision_count": 1},
            "sources": [
                {
                    "source_id": "traffic_collisions",
                    "source_name": "Traffic Collisions",
                    "version": "fixture",
                    "status": "available_local",
                    "date_range": "2014-2025",
                    "source_url": "https://example.test",
                }
            ],
            "methods": ["Fixture method"],
            "caveats": [{"caveat_id": "fixture", "text": "Fixture caveat"}],
            "refusals": [],
            "query_metadata": {"runtime_ms": 10.0},
        },
    }


def test_streamlit_submission_renders_packet_and_exports(monkeypatch) -> None:
    monkeypatch.setattr("trs.ui.app.answer_question", lambda *args, **kwargs: _response())
    script = Path(__file__).parents[1] / "scripts" / "run_analyst_ui.py"
    app = AppTest.from_file(str(script)).run(timeout=20)

    app.text_area[0].set_value("Give me a safety snapshot")
    app.button[0].click()
    app.run(timeout=20)

    assert not app.exception
    assert [item.value for item in app.success] == ["Status: ANSWERED"]
    assert {(item.label, item.value) for item in app.metric} == {
        ("Collision Count", "12"),
        ("Ksi Collision Count", "1"),
    }
    assert len(app.get("download_button")) == 2
