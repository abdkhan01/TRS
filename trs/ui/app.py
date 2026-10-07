from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from trs.storage.paths import default_duckdb_path
from trs.ui.exports import evidence_filename, to_json, to_markdown
from trs.ui.runtime import answer_question, log_export_event


TEMPLATES = {
    "Automatic — classify my question": None,
    "KSI trend": "ksi_trend",
    "Collision profile": "collision_profile",
    "Intersection safety snapshot": "intersection_safety_snapshot",
    "Corridor safety snapshot": "corridor_safety_snapshot",
    "Historical ASE context": "historical_ase_context",
    "Speed and volume context": "speed_volume_context",
    "Posted speed limit lookup": "posted_speed_limit_lookup",
    "Community Safety Zone status": "csz_status_lookup",
    "Turn restriction policy history": "turn_restriction_policy_history",
}


def _fallback_error(question: str, template_id: str | None, error: Exception) -> dict[str, Any]:
    return {
        "packet_id": "ui-runtime-error",
        "created_at": None,
        "question": question,
        "template_id": template_id or "automatic",
        "status": "error",
        "location": {
            "input": "",
            "resolved_name": None,
            "geometry": None,
            "geometry_type": "unresolved",
            "source_ids": [],
            "match_confidence": "unresolved",
            "method": "The request did not reach a completed location-resolution step.",
        },
        "parameters": {},
        "results": {"error": f"{type(error).__name__}: {error}"},
        "sources": [],
        "methods": [],
        "caveats": [],
        "refusals": [],
        "query_metadata": {},
    }


def _render_status(st: Any, response: dict[str, Any]) -> None:
    status = str(response.get("status", "unknown"))
    label = f"Status: {status.replace('_', ' ').upper()}"
    if status == "answered":
        st.success(label, icon="✅")
    elif status in {"partially_answered", "refused", "clarification"}:
        st.warning(label, icon="⚠️")
    else:
        st.error(label, icon="🚨")


def _render_results(st: Any, results: Any) -> None:
    st.subheader("Evidence")
    if not results:
        st.info("No evidence values were returned for this request.")
        return
    if not isinstance(results, dict):
        st.json(results)
        return

    scalar_items = [
        (key, value)
        for key, value in results.items()
        if value is None or isinstance(value, (str, int, float, bool))
    ]
    for start in range(0, len(scalar_items), 4):
        batch = scalar_items[start : start + 4]
        columns = st.columns(len(batch))
        for column, (key, value) in zip(columns, batch, strict=True):
            column.metric(key.replace("_", " ").title(), "—" if value is None else value)

    for key, value in results.items():
        if (key, value) in scalar_items:
            continue
        st.markdown(f"#### {key.replace('_', ' ').title()}")
        if isinstance(value, list) and value and all(isinstance(row, dict) for row in value):
            st.dataframe(value, width="stretch", hide_index=True)
        else:
            st.json(value)


def _render_refusals(st: Any, refusals: list[dict[str, Any]]) -> None:
    if not refusals:
        return
    st.subheader("Unsupported parts of the request")
    for refusal in refusals:
        reason = refusal.get("reason") or "The requested answer is not supported."
        st.error(str(reason), icon="⛔")
        alternative = refusal.get("allowed_alternative")
        if alternative:
            st.info(f"Available alternative: {alternative}")


def _render_review_panels(st: Any, packet: dict[str, Any]) -> None:
    location = packet.get("location") or {}
    parameters = packet.get("parameters") or {}
    sources = packet.get("sources") or []
    methods = packet.get("methods") or []
    caveats = packet.get("caveats") or []

    with st.expander("Location and assumptions", expanded=True):
        st.write(f"**Input:** {location.get('input') or 'Not provided'}")
        st.write(f"**Resolved location:** {location.get('resolved_name') or 'Unresolved'}")
        st.write(f"**Match confidence:** {location.get('match_confidence') or 'Not provided'}")
        st.write(f"**Method:** {location.get('method') or 'Not provided'}")
        if parameters:
            st.write("**Parameters**")
            st.json(parameters)

    with st.expander(f"Sources and versions ({len(sources)})", expanded=True):
        if sources:
            st.dataframe(
                [
                    {
                        "Source": source.get("source_name"),
                        "ID": source.get("source_id"),
                        "Version": source.get("version"),
                        "Status": source.get("status"),
                        "Date range": source.get("date_range"),
                        "URL": source.get("source_url"),
                    }
                    for source in sources
                ],
                width="stretch",
                hide_index=True,
            )
        else:
            st.info("No sources were attached to this response.")

    with st.expander(f"Methods ({len(methods)})"):
        if methods:
            for method in methods:
                st.write(f"- {method}")
        else:
            st.info("No method notes were returned.")

    with st.expander(f"Caveats ({len(caveats)})", expanded=bool(caveats)):
        if caveats:
            for caveat in caveats:
                st.warning(str(caveat.get("text") or caveat), icon="⚠️")
        else:
            st.info("No caveats were returned.")

    with st.expander("Reproducibility details"):
        st.json(packet.get("query_metadata") or {})


def _render_exports(st: Any, packet: dict[str, Any], log_path: Path | None) -> None:
    st.subheader("Copy or download")
    json_export = to_json(packet)
    markdown_export = to_markdown(packet)
    json_tab, markdown_tab = st.tabs(["JSON", "Markdown"])
    with json_tab:
        st.caption("Use the copy control on the code block, or download the file.")
        st.code(json_export, language="json")
        callback = ({"on_click": log_export_event, "args": (log_path, packet, "json")} if log_path else {})
        st.download_button(
            "Download JSON",
            json_export,
            file_name=evidence_filename(packet, "json"),
            mime="application/json",
            **callback,
        )
    with markdown_tab:
        st.caption("Use the copy control on the code block, or download the file.")
        st.code(markdown_export, language="markdown")
        callback = ({"on_click": log_export_event, "args": (log_path, packet, "markdown")} if log_path else {})
        st.download_button(
            "Download Markdown",
            markdown_export,
            file_name=evidence_filename(packet, "md"),
            mime="text/markdown",
            **callback,
        )


def run_app() -> None:
    import streamlit as st

    st.set_page_config(
        page_title="Vision Zero Copilot",
        page_icon="🚦",
        layout="wide",
    )
    st.title("Vision Zero Copilot")
    st.caption("Local, deterministic road-safety evidence for analyst review")

    with st.sidebar:
        st.header("Local settings")
        db_path_text = st.text_input(
            "DuckDB path",
            value=os.environ.get("TRS_DB_PATH", str(default_duckdb_path())),
            help="Path to the locally ingested Vision Zero DuckDB database.",
        )
        log_path_text = st.text_input(
            "Audit log path (optional)",
            value=os.environ.get(
                "TRS_COPILOT_LOG_PATH",
                str(default_duckdb_path().parent / "audit" / "copilot.jsonl"),
            ),
        )
        st.caption("Data and processing remain on this machine.")

    with st.form("analyst_question"):
        question = st.text_area(
            "Question",
            placeholder="Show the citywide KSI trend from 2019 to 2023",
            height=100,
        )
        template_label = st.selectbox("Evidence template", options=list(TEMPLATES))
        location_text = st.text_input(
            "Location (optional)",
            placeholder=(
                "Intersection: Bloor St W and Keele St; corridor: "
                "King St W from Spadina Ave to Bathurst St"
            ),
        )
        date_left, date_right, buffer_column = st.columns(3)
        with date_left:
            start_year = st.number_input("Start year", min_value=2000, max_value=2100, value=2019)
        with date_right:
            end_year = st.number_input("End year", min_value=2000, max_value=2100, value=2023)
        with buffer_column:
            buffer_meters = st.number_input(
                "Location buffer (metres)", min_value=1, max_value=1000, value=50
            )
        submitted = st.form_submit_button("Run evidence query", type="primary")

    if submitted:
        if not question.strip():
            st.warning("Enter a question before running the evidence query.", icon="⚠️")
        elif start_year > end_year:
            st.warning("Start year must be earlier than or equal to end year.", icon="⚠️")
        else:
            template_id = TEMPLATES[template_label]
            try:
                with st.spinner("Building the evidence packet…"):
                    response = answer_question(
                        Path(db_path_text).expanduser(),
                        question.strip(),
                        template_id=template_id,
                        location_text=location_text.strip() or None,
                        start_year=int(start_year),
                        end_year=int(end_year),
                        buffer_meters=int(buffer_meters) if location_text.strip() else None,
                        log_path=(
                            Path(log_path_text).expanduser()
                            if log_path_text.strip()
                            else None
                        ),
                    )
            except Exception as exc:
                packet = _fallback_error(question.strip(), template_id, exc)
                response = {
                    "status": "error",
                    "summary": "The local analyst application could not complete the request.",
                    "packet": packet,
                    "metrics": {},
                }
            st.session_state["last_copilot_response"] = response

    response = st.session_state.get("last_copilot_response")
    if response:
        st.divider()
        _render_status(st, response)
        if response.get("summary"):
            st.markdown("### Evidence summary")
            st.write(response["summary"])
        packet = response.get("packet")
        if not packet:
            st.info("No evidence packet was run. Update the request using the clarification above.")
            return
        error = (packet.get("results") or {}).get("error")
        if error:
            st.error(f"Query error: {error}")
        _render_refusals(st, packet.get("refusals") or [])
        _render_results(st, packet.get("results") or {})
        _render_review_panels(st, packet)
        _render_exports(
            st,
            packet,
            Path(log_path_text).expanduser() if log_path_text.strip() else None,
        )
    else:
        st.info(
            "Ask a question to create an evidence packet. Unsupported requests "
            "return a visible refusal."
        )
