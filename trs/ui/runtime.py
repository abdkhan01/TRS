from __future__ import annotations

from pathlib import Path
from typing import Any


def answer_question(
    db_path: Path,
    question: str,
    *,
    template_id: str | None = None,
    location_text: str | None = None,
    start_year: int | None = None,
    end_year: int | None = None,
    buffer_meters: int | None = None,
    log_path: Path | None = None,
) -> dict[str, Any]:
    """Call the copilot service while keeping it and Streamlit out of pure tests."""
    from trs.copilot.service import CopilotService

    service = CopilotService(db_path, resolver=None, log_path=log_path)
    return service.answer(
        question,
        template_id=template_id,
        location_text=location_text,
        start_year=start_year,
        end_year=end_year,
        buffer_meters=buffer_meters,
    )
