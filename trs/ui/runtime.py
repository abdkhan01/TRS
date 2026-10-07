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
    from trs.geo.resolver import LocationResolver

    service = CopilotService(
        db_path,
        resolver=LocationResolver(db_path),
        log_path=log_path,
    )
    return service.answer(
        question,
        template_id=template_id,
        location_text=location_text,
        start_year=start_year,
        end_year=end_year,
        buffer_meters=buffer_meters,
    )


def log_export_event(
    log_path: Path,
    packet: dict[str, Any],
    export_format: str,
) -> None:
    """Append a small audit event when an analyst downloads an evidence packet."""
    from trs.copilot.audit import JsonlAuditLogger

    JsonlAuditLogger(log_path, include_question=False).append(
        {
            "event_type": "export",
            "status": packet.get("status"),
            "template_id": packet.get("template_id"),
            "packet_id": packet.get("packet_id"),
            "export_format": export_format,
        }
    )
