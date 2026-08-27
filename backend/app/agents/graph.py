from typing import TypedDict, List, Dict, Any, Optional
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

class AgentState(TypedDict):
    session_id: str
    user_query: str
    language: str
    persona: str
    slots: Dict[str, Any] # location, time_window, boat_id
    sources_used: List[str]
    trace_steps: List[str]
    hinge_events: List[Dict[str, Any]]
    computed_metrics: Dict[str, Any] # index, return_window, turn_back_time, raw_hs, etc.
    verdict: str
    llm_output: Dict[str, Any] # intent, slots, explanation_text, verdict_token
    guard_result: str # PASS / REJECT
    final_response: Dict[str, Any]

def PlannerNode(state: AgentState) -> AgentState:
    # Retain existing fields and augment
    state['trace_steps'] = state.get('trace_steps', []) + ["PlannerNode: Extracting intent and slots"]
    
    current_slots = state.get('slots', {})
    
    state['llm_output'] = state.get('llm_output', {})
    state['llm_output']['intent'] = "safety_check"
    
    return state

def DiscoveryNode(state: AgentState) -> AgentState:
    state['trace_steps'] = state.get('trace_steps', []) + ["DiscoveryNode: Selecting data sources"]
    state['sources_used'] = state.get('sources_used', []) + ["MOSDAC"]
    return state

def WeatherNode(state: AgentState) -> AgentState:
    state['trace_steps'] = state.get('trace_steps', []) + ["WeatherNode: Fetching wind and atmospheric data"]
    return state

def OceanNode(state: AgentState) -> AgentState:
    state['trace_steps'] = state.get('trace_steps', []) + ["OceanNode: Fetching wave and tide data"]
    state['computed_metrics'] = state.get('computed_metrics', {})
    state['computed_metrics']['raw_hs'] = 2.5
    state['computed_metrics']['tp'] = 10.0
    return state

def GeospatialNode(state: AgentState) -> AgentState:
    state['trace_steps'] = state.get('trace_steps', []) + ["GeospatialNode: IMBL/MPA geofence and PFZ checks"]
    return state

def RiskNode(state: AgentState) -> AgentState:
    state['trace_steps'] = state.get('trace_steps', []) + ["RiskNode: Calculating hazard index and verdict"]
    
    # Mock Risk calculation
    index = 0.45
    verdict = "MARGINAL"
    
    # Detect Hinge Event (e.g., if hs caused verdict to flip from SAFE to MARGINAL)
    state['hinge_events'] = state.get('hinge_events', [])
    state['hinge_events'].append({
        "variable": "raw_hs",
        "threshold_crossed": True,
        "impact": "Verdict shifted to MARGINAL"
    })
    
    state['computed_metrics'] = state.get('computed_metrics', {})
    state['computed_metrics']['index'] = index
    state['verdict'] = verdict
    return state

def RoutingNode(state: AgentState) -> AgentState:
    state['trace_steps'] = state.get('trace_steps', []) + ["RoutingNode: Computing least-cost H3 corridor"]
    state['computed_metrics'] = state.get('computed_metrics', {})
    state['computed_metrics']['return_window'] = "08:00 - 12:00"
    state['computed_metrics']['turn_back_time'] = "11:00"
    return state

def SynthesisNode(state: AgentState) -> AgentState:
    state['trace_steps'] = state.get('trace_steps', []) + ["SynthesisNode: Drafting localized explanation"]
    
    state['llm_output'] = state.get('llm_output', {})
    state['llm_output']['explanation_text'] = "Conditions are marginal due to wave height."
    state['llm_output']['verdict_token'] = state.get('verdict', 'SAFE') 
    return state

def GuardNode(state: AgentState) -> AgentState:
    state['trace_steps'] = state.get('trace_steps', []) + ["GuardNode: Enforcing deterministic safety"]
    
    llm_verdict = state.get('llm_output', {}).get('verdict_token')
    deterministic_verdict = state.get('verdict')
    
    if llm_verdict == deterministic_verdict:
        state['guard_result'] = "PASS"
        state['final_response'] = {
            "status": "success",
            "message": state['llm_output'].get('explanation_text'),
            "verdict": deterministic_verdict,
            "metrics": state.get('computed_metrics', {})
        }
    else:
        state['guard_result'] = "REJECT"
        state['final_response'] = {
            "status": "fallback",
            "message": "System safety mismatch detected. Falling back to official INCOIS/IMD advisory.",
            "verdict": deterministic_verdict,
            "metrics": state.get('computed_metrics', {})
        }
        
    return state

workflow = StateGraph(AgentState)

workflow.add_node("planner", PlannerNode)
workflow.add_node("discovery", DiscoveryNode)
workflow.add_node("weather", WeatherNode)
workflow.add_node("ocean", OceanNode)
workflow.add_node("geospatial", GeospatialNode)
workflow.add_node("risk", RiskNode)
workflow.add_node("routing", RoutingNode)
workflow.add_node("synthesis", SynthesisNode)
workflow.add_node("guard", GuardNode)

workflow.add_edge("planner", "discovery")
workflow.add_edge("discovery", "weather")
workflow.add_edge("weather", "ocean")
workflow.add_edge("ocean", "geospatial")
workflow.add_edge("geospatial", "risk")
workflow.add_edge("risk", "routing")
workflow.add_edge("routing", "synthesis")
workflow.add_edge("synthesis", "guard")
workflow.add_edge("guard", END)

workflow.set_entry_point("planner")

memory = MemorySaver()
app = workflow.compile(checkpointer=memory)
