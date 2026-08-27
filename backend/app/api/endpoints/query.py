import uuid
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.schemas.query import QueryRequest, QueryResponse
from backend.app.db.session import get_db
from backend.app.models.query import Query
from backend.app.models.trace import Trace
from backend.app.agents.graph import app as agent_app, AgentState
from datetime import datetime

router = APIRouter()

@router.post("", response_model=QueryResponse)
async def execute_query(request: QueryRequest, db: AsyncSession = Depends(get_db)):
    """Executes the LangGraph agent graph and returns the decision."""
    
    # Save query to DB
    db_query = Query(
        session_id=request.session_id,
        text=request.query_text,
        lang="en",
        intent="safety_check",
        slots={}
    )
    db.add(db_query)
    
    # Run graph
    initial_state = AgentState(
        session_id=str(request.session_id),
        user_query=request.query_text,
        language="en",
        persona="default",
        slots={},
        sources_used=[],
        trace_steps=[],
        hinge_events=[],
        computed_metrics={},
        verdict="",
        llm_output={},
        guard_result="",
        final_response={}
    )
    
    config = {"configurable": {"thread_id": str(request.session_id)}}
    result_state = agent_app.invoke(initial_state, config=config)
    
    # Save trace
    trace = Trace(
        nodes={"steps": result_state.get("trace_steps", [])},
        hinge_events={"events": result_state.get("hinge_events", [])}
    )
    db.add(trace)
    await db.flush()
    
    db_query.trace_id = trace.trace_id
    
    await db.commit()
    await db.refresh(trace)
    
    return QueryResponse(
        answer=result_state.get("final_response", {}).get("message", ""),
        verdict=result_state.get("verdict", "UNKNOWN"),
        return_window={"window": result_state.get("computed_metrics", {}).get("return_window")},
        trace_id=trace.trace_id,
        guard={"status": result_state.get("guard_result", "UNKNOWN")},
        sources=[{"name": s} for s in result_state.get("sources_used", [])],
        layers=["weather", "ocean", "geospatial"]
    )
