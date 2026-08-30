from datetime import datetime, timezone
from typing import Any, Dict

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.agents.graph import run_query
from backend.app.core import config_store
from backend.app.core.advisory_engine import build_advisory
from backend.app.core.broadcast import render_all
from backend.app.core.discovery import DatasetDiscoveryAgent
from backend.app.core.intents import answer_for_intent
from backend.app.core.nlu import parse_utterance
from backend.app.core.official import advisory_for_date
from backend.app.db.session import get_db
from backend.app.models.advisory import Advisory
from backend.app.models.query import Query
from backend.app.models.session import Session as SessionModel
from backend.app.models.trace import Trace
from backend.app.schemas.query import QueryRequest, QueryResponse

router = APIRouter()

# Variables the crossing verdict needs. The discovery agent resolves these
# against the registry at query time rather than reading a fixed source.
CROSSING_VARIABLES = ["hs", "tp", "dir", "swell_hs"]


@router.post("")
async def execute_query(request: QueryRequest, db: AsyncSession = Depends(get_db)):
    """Runs the agent graph and persists the query, trace and advisory."""
    session = await _load_or_create_session(db, request)
    context: Dict[str, Any] = dict(session.context or {})
    if request.user_lat is not None and request.user_lon is not None:
        context["user_lat"] = request.user_lat
        context["user_lon"] = request.user_lon
    if request.gps_error is not None:
        context["gps_error"] = request.gps_error

    # Discovery runs against the live registry before the graph, so the graph
    # itself stays serialisable and the decision appears as its own trace node.
    agent = DatasetDiscoveryAgent(session=db)
    result = await agent.discover_sources(CROSSING_VARIABLES, "kerala")
    discovery = {
        "required_variables": CROSSING_VARIABLES,
        "region": "kerala",
        "log": {
            "candidates_considered": result.log.candidates_considered,
            "chosen_source": result.log.chosen_source,
            "priority_tier": result.log.priority_tier,
            "reason": result.log.reason,
            "fallback_occurred": result.log.fallback_occurred,
            "failed": result.log.failed,
            "per_variable": result.log.per_variable,
        },
        "sources": [_source_view(s) for s in result.selected_sources],
    }

    parsed = parse_utterance(request.query_text, context)
    target_date = parsed["slots"]["date"]
    official = await advisory_for_date(target_date)

    state = await run_query(
        user_query=request.query_text,
        session_id=str(session.session_id),
        context=context,
        persona=request.persona or session.persona or "fisherman",
        discovery=discovery,
        official_advisory=official,
        force_failure=bool(request.force_failure),
    )

    computed = state["computed"]

    # The planner classifies intent; honour it. Without this every question -
    # including "where is the nearest fishing zone?" - came back as a crossing
    intent = state.get("llm_output", {}).get("intent", "crossing_safety")
    intent_result = await answer_for_intent(intent, state["slots"], computed["cruise_knots"])

    # Persist the merged context so the next turn inherits it (FR-03).
    session.context = state["slots"]
    session.persona = request.persona or session.persona
    session.language = state.get("language", session.language)

    trace = Trace(
        nodes={"steps": state.get("trace_steps", [])},
        hinge_events={"events": state.get("hinge_events", [])},
    )
    db.add(trace)
    await db.flush()

    db.add(Query(
        session_id=session.session_id,
        text=request.query_text,
        lang=state.get("language", "en"),
        intent=state.get("llm_output", {}).get("intent", "crossing_safety"),
        slots=state["slots"],
        trace_id=trace.trace_id,
    ))

    advisory = Advisory(
        boat_id=None,
        inlet_id=computed["inlet_id"],
        verdict=computed["verdict"],
        index_value=computed["index_value"],
        return_window=computed.get("return_window") or {},
        turn_back_time=computed.get("turn_back_label") or "",
        state="PENDING_RELEASE",
        guard_result=state.get("guard_result", "UNKNOWN"),
        hull_class=computed["hull_class"],
        advisory_date=computed["date"],
        payload=_persistable(computed),
    )
    db.add(advisory)
    await db.flush()
    await db.commit()

    disagreement = _disagrees(computed["verdict"], official.get("severity"))

    # For a non-crossing intent the crossing advisory is still computed and still
    # guarded - it stays on screen as context - but the answer addresses the
    # question that was actually asked.
    answer_text = state["final_response"]["message"]
    if intent_result and state.get("guard_result") != "REJECT":
        answer_text = intent_result["answer"]

    lang = state.get("language", "en")
    if lang != "en":
        import os
        import httpx
        api_key = os.environ.get("GROQ_API_KEY")
        if api_key:
            target_lang = "Malayalam" if lang == "ml" else "Tamil"
            try:
                with httpx.Client() as client:
                    resp = client.post(
                        "https://api.groq.com/openai/v1/chat/completions",
                        headers={"Authorization": f"Bearer {api_key}"},
                        json={
                            "model": "llama3-8b-8192",
                            "messages": [
                                {"role": "system", "content": f"You are a translator. Translate the following text to {target_lang}. Respond ONLY with the translated text, no other comments."},
                                {"role": "user", "content": answer_text}
                            ]
                        },
                        timeout=10.0
                    )
                    if resp.status_code == 200:
                        data = resp.json()
                        answer_text = data["choices"][0]["message"]["content"].strip()
            except Exception:
                pass

    from fastapi.responses import StreamingResponse
    import json
    import asyncio

    response_obj = QueryResponse(
        answer=answer_text,
        verdict=computed["verdict"],
        index_value=computed["index_value"],
        hull_class=computed["hull_class"],
        hull_label=computed["hull_label"],
        date=computed["date"],
        return_window=computed.get("return_window"),
        turn_back_time=computed.get("turn_back_label"),
        trace_id=trace.trace_id,
        advisory_id=advisory.advisory_id,
        guard={"result": state.get("guard_result"), "reason": state.get("guard_reason")},
        sources=discovery["sources"],
        discovery_log=discovery["log"],
        layers=state.get("layers", []),
        language=state.get("language", "en"),
        intent=state.get("llm_output", {}).get("intent"),
        context=state["slots"],
        updated_fields=parsed["updated_fields"],
        hourly=computed["hourly"],
        hull_comparison=state.get("hull_comparison", []),
        official_advisory=official,
        disagreement=disagreement,
        hinge_events=state.get("hinge_events", []),
        provenance=computed["provenance"],
        date_mapped_from_request=computed["date_mapped_from_request"],
        broadcast=render_all(computed, state.get("hull_comparison", [])),
        intent_result=intent_result,
    )

    async def stream_generator():
        # Stream the text chunk by chunk to simulate real-time typing
        words = answer_text.split(" ")
        for i, word in enumerate(words):
            chunk = word + (" " if i < len(words) - 1 else "")
            yield f"data: {json.dumps({'type': 'chunk', 'text': chunk})}\n\n"
            await asyncio.sleep(0.03)
        
        # Yield the final structured data payload
        payload = response_obj.model_dump(mode="json")
        yield f"data: {json.dumps({'type': 'done', 'payload': payload})}\n\n"

    if request.stream:
        return StreamingResponse(stream_generator(), media_type="text/event-stream")
    return response_obj


def _persistable(computed: Dict[str, Any]) -> Dict[str, Any]:
    """Drop the bulky hourly series before storing the advisory payload."""
    return {k: v for k, v in computed.items() if k not in ("hourly", "_numerals")}


def _source_view(s: Any) -> Dict[str, Any]:
    return {
        "source_id": s.source_id,
        "provider": s.provider,
        "country": s.country,
        "variables": s.variables,
        "resolution_km": s.resolution_km,
        "access_status": s.access_status,
        "priority_tier": s.priority_tier,
        "provenance": getattr(s, "provenance", "ORCA_LIVE"),
        "last_pull_ts": getattr(s, "last_pull_ts", None),
    }


def _disagrees(verdict: str, severity: str) -> bool:
    """FR-19: highlight when ORCA and the official bulletin do not line up."""
    official_blocking = severity in ("warning", "severe")
    orca_blocking = verdict == "DO_NOT_CROSS"
    return official_blocking != orca_blocking


async def _load_or_create_session(db: AsyncSession, request: QueryRequest) -> SessionModel:
    if request.session_id:
        found = await db.execute(
            select(SessionModel).filter(SessionModel.session_id == request.session_id))
        existing = found.scalars().first()
        if existing:
            return existing
    session = SessionModel(
        session_id=request.session_id,
        language="en",
        persona=request.persona or "fisherman",
        context={},
    )
    db.add(session)
    await db.flush()
    return session
