"""The ORCA agent graph.

Every node here delegates to the deterministic core - `hazard_engine`,
`advisory_engine`, `guard`, `discovery` - rather than restating its result.
Nothing in this file decides a verdict on its own.

Trace nodes record what each agent actually received and produced, and hinge
detection is a real counterfactual: the index is recomputed with one input
neutralised, and a hinge is recorded only when doing so changes the verdict.
"""
import time
import os
import json
import httpx
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, TypedDict

from langgraph.graph import END, StateGraph

from backend.app.core import config_store
from backend.app.core.advisory_engine import build_advisory, compare_hulls
from backend.app.core.dataset import INLET
from backend.app.core.guard import validate_advisory
from backend.app.core.hazard_engine import calculate_hazard_index, evaluate_verdict
from backend.app.core.nlu import parse_utterance


class AgentState(TypedDict, total=False):
    session_id: str
    user_query: str
    language: str
    persona: str
    slots: Dict[str, Any]
    discovery: Dict[str, Any]
    official_advisory: Dict[str, Any]
    force_failure: bool
    sources_used: List[Dict[str, Any]]
    trace_steps: List[Dict[str, Any]]
    hinge_events: List[Dict[str, Any]]
    computed: Dict[str, Any]
    verdict: str
    llm_output: Dict[str, Any]
    guard_result: str
    guard_reason: str
    layers: List[str]
    final_response: Dict[str, Any]


def _step(state: AgentState, agent: str, inp: Any, out: Any, started: float,
          hinge: Optional[Dict[str, Any]] = None) -> None:
    state.setdefault("trace_steps", []).append({
        "agent": agent,
        "input": inp,
        "output": out,
        "ms": round((time.perf_counter() - started) * 1000, 1),
        "hinge": hinge,
    })


# --------------------------------------------------------------------------
# Nodes
# --------------------------------------------------------------------------

def planner_node(state: AgentState) -> AgentState:
    t0 = time.perf_counter()
    parsed = parse_utterance(state.get("user_query", ""), state.get("slots") or {})
    state["slots"] = parsed["slots"]
    state["language"] = parsed["language"]
    state["llm_output"] = {"intent": parsed["intent"], "slots": parsed["slots"]}
    state["layers"] = parsed["layers"]
    _step(state, "Planner", {"utterance": state.get("user_query")},
          {"intent": parsed["intent"], "language": parsed["language"],
           "slots": parsed["slots"], "updated_fields": parsed["updated_fields"]}, t0)
    return state


def discovery_node(state: AgentState) -> AgentState:
    """Surfaces the source selection that ran ahead of the graph (SRS 5.2)."""
    t0 = time.perf_counter()
    d = state.get("discovery") or {}
    log = d.get("log", {})
    hinge = None
    if log.get("fallback_occurred"):
        hinge = {
            "type": "SOURCE_SUBSTITUTION",
            "cause": (f"Tier-1 source(s) {', '.join(log.get('failed', [])) or 'unavailable'} "
                      f"failed to connect, so the Weather agent read "
                      f"{log.get('chosen_source')} (tier {log.get('priority_tier')}) instead. "
                      f"Every downstream number comes from the substitute."),
        }
    state["sources_used"] = d.get("sources", [])
    _step(state, "Discovery",
          {"required_variables": d.get("required_variables", []), "region": d.get("region")},
          {"candidates_considered": log.get("candidates_considered", []),
           "chosen_source": log.get("chosen_source"),
           "priority_tier": log.get("priority_tier"),
           "reason": log.get("reason"),
           "fallback_occurred": log.get("fallback_occurred", False)}, t0, hinge)
    if hinge:
        state.setdefault("hinge_events", []).append(hinge)
    return state


def weather_node(state: AgentState) -> AgentState:
    t0 = time.perf_counter()
    adv = state["computed"]
    _step(state, "Weather", {"inlet": INLET["name"], "date": adv["date"]},
          {"wind_ms": adv["wind_ms"], "lightning_flag": adv["lightning_flag"],
           "cyclone_flag": adv["cyclone_flag"]}, t0)
    return state


def ocean_node(state: AgentState) -> AgentState:
    t0 = time.perf_counter()
    adv = state["computed"]
    _step(state, "Ocean", {"inlet": INLET["name"], "date": adv["date"]},
          {"hs_m": adv["hs_m"], "tp_s": adv["tp_s"], "dir_deg": adv["dir_deg"],
           "swell_hs_m": adv["swell_hs_m"], "tide_stage": adv["tide_stage"]}, t0)
    return state


def geospatial_node(state: AgentState) -> AgentState:
    t0 = time.perf_counter()
    adv = state["computed"]
    _step(state, "Geospatial",
          {"inlet": INLET["name"], "channel_bearing_deg": INLET["channel_bearing_deg"]},
          {"wave_channel_offset_deg": round(abs(adv["dir_deg"] - INLET["channel_bearing_deg"]), 1),
           "mouth_width_m": INLET["mouth_width_m"]}, t0)
    return state


def risk_node(state: AgentState) -> AgentState:
    """Banding is already computed; this node records it and tests hinges."""
    t0 = time.perf_counter()
    adv = state["computed"]
    band = config_store.band_for(adv["hull_class"])
    verdict = adv["verdict"]
    state["verdict"] = verdict

    hinge = _detect_hinge(adv, band, verdict)
    if hinge:
        state.setdefault("hinge_events", []).append(hinge)

    _step(state, "Risk",
          {"hs_m": adv["hs_m"], "tp_s": adv["tp_s"], "dir_deg": adv["dir_deg"],
           "tide_stage": adv["tide_stage"], "hull_class": adv["hull_class"]},
          {"index_value": adv["index_value"], "verdict": verdict,
           "index_marginal": band.index_marginal, "index_unsafe": band.index_unsafe}, t0, hinge)
    return state


def _detect_hinge(adv: Dict[str, Any], band: Any, verdict: str) -> Optional[Dict[str, Any]]:
    """A hinge is recorded only if removing one input actually flips the verdict."""
    base_wave = {"hs": adv["hs_m"], "tp": adv["tp_s"], "dir": adv["dir_deg"],
                 "swell_hs": adv["swell_hs_m"]}
    geom = {"channel_bearing": adv["channel_bearing_deg"]}

    # Counterfactual 1: no storm flag.
    if adv["lightning_flag"] or adv["cyclone_flag"]:
        alt = calculate_hazard_index(base_wave, {"stage": adv["tide_stage"], "rate": 0.3},
                                     geom, 0, 0)
        alt_verdict = evaluate_verdict(alt, band)
        if alt_verdict != verdict:
            trigger = "an active cyclone warning" if adv["cyclone_flag"] else "a lightning detection"
            return {
                "type": "STORM_OVERRIDE",
                "cause": (f"The Weather agent reported {trigger} inside the alert radius. "
                          f"That saturates the index at {adv['index_value']}, taking the Risk "
                          f"agent's verdict from {alt_verdict} to {verdict} regardless of "
                          f"wave state."),
            }

    # Counterfactual 2: slack water instead of the observed tide stage.
    if adv["tide_stage"] == "ebb":
        alt = calculate_hazard_index(base_wave, {"stage": "slack", "rate": 0.0}, geom,
                                     adv["lightning_flag"], adv["cyclone_flag"])
        alt_verdict = evaluate_verdict(alt, band)
        if alt_verdict != verdict:
            return {
                "type": "EBB_TIDE",
                "cause": (f"The Ocean agent found the tide ebbing at the peak hour. On slack "
                          f"water the same {adv['hs_m']} m swell scores {round(alt, 3)} and "
                          f"reads {alt_verdict}; the ebb penalty lifts it to "
                          f"{adv['index_value']}, which changed the Risk agent's verdict to "
                          f"{verdict}."),
            }

    # Counterfactual 3: the hull itself.
    others = [r for r in config_store.hull_thresholds() if r["hull_class"] != adv["hull_class"]]
    for row in others:
        alt_verdict = evaluate_verdict(adv["index_value"], config_store.ThresholdBand(row))
        if alt_verdict != verdict:
            return {
                "type": "HULL_THRESHOLD",
                "cause": (f"At index {adv['index_value']} the Risk agent reads {verdict} for a "
                          f"{adv['hull_label']} (unsafe at {adv['index_unsafe']}), but "
                          f"{alt_verdict} for a {row['label']} (unsafe at {row['index_unsafe']}). "
                          f"The boat profile, not the weather, decided this answer."),
            }
    return None


def routing_node(state: AgentState) -> AgentState:
    t0 = time.perf_counter()
    adv = state["computed"]
    _step(state, "Routing",
          {"cruise_knots": adv["cruise_knots"], "distance_nm": adv["distance_nm"]},
          {"return_window": adv["return_window"], "turn_back_time": adv["turn_back_label"]}, t0)
    return state


def synthesis_node(state: AgentState) -> AgentState:
    """Assembles the explanation by template substitution or Groq LLM (SRS 5.5)."""
    t0 = time.perf_counter()
    adv = state["computed"]
    text = adv["explanation"]
    token = adv["verdict"]

    api_key = os.environ.get("GROQ_API_KEY")
    if api_key and not state.get("force_failure"):
        try:
            with httpx.Client() as client:
                persona_config = config_store.persona(state.get('persona') or 'fisherman')
                framing = persona_config.get('answer_framing', '')
                prompt = f"""
You are an expert coastal safety advisor for the ORCA project.
The user asked: "{state.get('user_query')}"

Computed Conditions:
- Inlet: {adv.get('inlet_name')}
- Boat/Hull Class: {adv.get('hull_label')}
- Verdict: {adv.get('verdict')}
- Hazard Index: {adv.get('index_value')} (Limit for this hull: {adv.get('index_unsafe')})
- Swell: {adv.get('hs_m')} m at {adv.get('tp_s')} s
- Tide: {adv.get('tide_stage')} tide at peak hour ({adv.get('peak_hour')}:00)
- Cyclone Warning: {'Yes' if adv.get('cyclone_flag') else 'No'}
- Lightning: {'Yes' if adv.get('lightning_flag') else 'No'}
- Turn-back time: {adv.get('turn_back_label') or 'N/A'}
- Safe crossing window: {adv.get('return_window', {}).get('start_label', 'N/A') if adv.get('return_window') else 'N/A'} to {adv.get('return_window', {}).get('end_label', 'N/A') if adv.get('return_window') else 'N/A'}

Response Framing:
{framing}

Formulate a concise, clear answer addressing the user's question, using the computed conditions above.
CRITICAL: Do not include ANY numbers (including percentages or counts like 100%, 1, 2) in your response that are not explicitly provided in the Computed Conditions above. The safety guard will reject your response if it contains unauthorized numbers.
Ensure you strictly respond in JSON format with two keys:
1. "explanation_text": Your detailed but concise response. Do not repeat the prompt.
2. "verdict_token": The exact verdict token ("SAFE", "MARGINAL", or "DO_NOT_CROSS").
"""
                resp = client.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "openai/gpt-oss-20b",
                        "messages": [{"role": "system", "content": prompt}],
                        "response_format": {"type": "json_object"},
                        "reasoning_format": "hidden"
                    },
                    timeout=15.0
                )
                if resp.status_code == 200:
                    data = resp.json()
                    content_str = data["choices"][0]["message"]["content"]
                    # Clean up potential markdown formatting
                    content_str = content_str.strip()
                    if content_str.startswith("```json"):
                        content_str = content_str[7:]
                    if content_str.startswith("```"):
                        content_str = content_str[3:]
                    if content_str.endswith("```"):
                        content_str = content_str[:-3]
                    content_str = content_str.strip()
                    content = json.loads(content_str)
                    text = content.get("explanation_text", text)
                    token = content.get("verdict_token", token)
                else:
                    print(f"Groq API returned status {resp.status_code}: {resp.text}")
        except Exception as e:
            print(f"Groq API exception: {e}")

    if state.get("force_failure"):
        token = "SAFE" if adv["verdict"] != "SAFE" else "DO_NOT_CROSS"
        text = (f"Conditions at {adv['inlet_name']} are clear and the bar is safe to cross "
                f"at any time today.")

    state["llm_output"] = {**state.get("llm_output", {}),
                           "explanation_text": text, "verdict_token": token}
    _step(state, "Synthesis",
          {"verdict": adv["verdict"], "forced_failure": bool(state.get("force_failure"))},
          {"verdict_token": token, "chars": len(text)}, t0)
    return state


def guard_node(state: AgentState) -> AgentState:
    t0 = time.perf_counter()
    adv = state["computed"]
    official = state.get("official_advisory") or {}
    result = validate_advisory(state["llm_output"], adv, official)

    state["guard_result"] = "PASS" if result.status == "PASS" else "REJECT"
    state["guard_reason"] = result.reason
    state["final_response"] = {
        "status": "success" if result.status == "PASS" else "fallback",
        "message": result.final_text,
        "verdict": adv["verdict"],
    }
    _step(state, "Guard",
          {"verdict_token": state["llm_output"].get("verdict_token"),
           "computed_verdict": adv["verdict"],
           "staleness_hours": adv.get("staleness_hours", 0.0)},
          {"result": state["guard_result"], "reason": result.reason}, t0)
    return state


workflow = StateGraph(AgentState)
for name, fn in [
    ("planner", planner_node), ("discovery", discovery_node), ("weather", weather_node),
    ("ocean", ocean_node), ("geospatial", geospatial_node), ("risk", risk_node),
    ("routing", routing_node), ("synthesis", synthesis_node), ("guard", guard_node),
]:
    workflow.add_node(name, fn)

for a, b in [("planner", "discovery"), ("discovery", "weather"), ("weather", "ocean"),
             ("ocean", "geospatial"), ("geospatial", "risk"), ("risk", "routing"),
             ("routing", "synthesis"), ("synthesis", "guard"), ("guard", END)]:
    workflow.add_edge(a, b)

workflow.set_entry_point("planner")

# No checkpointer: conversational context is held in the `session` row, which is
# the thing the Context chips render, so there is one source of truth for it.
app = workflow.compile()


def run_query(
    user_query: str,
    session_id: str,
    context: Dict[str, Any],
    persona: str,
    discovery: Dict[str, Any],
    official_advisory: Dict[str, Any],
    force_failure: bool = False,
) -> AgentState:
    """Entry point used by /api/query."""
    parsed = parse_utterance(user_query, context)
    hull = parsed["slots"].get("hull_class") or "FRP_SMALL"
    target = datetime.fromisoformat(parsed["slots"]["date"]).replace(tzinfo=timezone.utc)

    computed = build_advisory(hull, target)
    computed["staleness_hours"] = 0.0

    state: AgentState = {
        "session_id": session_id,
        "user_query": user_query,
        "language": parsed["language"],
        "persona": persona,
        "slots": context,
        "discovery": discovery,
        "official_advisory": official_advisory,
        "force_failure": force_failure,
        "computed": computed,
        "trace_steps": [],
        "hinge_events": [],
    }
    result = app.invoke(state)
    result["hull_comparison"] = compare_hulls(target)
    return result
