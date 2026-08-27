import re
from typing import List, Any
from pydantic import BaseModel

class GuardEvaluation(BaseModel):
    status: str
    reason: str
    final_text: str
    state: str

def extract_numbers(text: str) -> List[float]:
    """Extracts all numerical tokens from text (integers and decimals)."""
    matches = re.findall(r'\d+(?:\.\d+)?', str(text))
    return [float(m) for m in matches]

def get_all_payload_numbers(payload: Any) -> List[float]:
    """Recursively extracts all numeric values from a payload."""
    nums = []
    if isinstance(payload, dict):
        for v in payload.values():
            nums.extend(get_all_payload_numbers(v))
    elif isinstance(payload, list):
        for item in payload:
            nums.extend(get_all_payload_numbers(item))
    elif isinstance(payload, (int, float)) and not isinstance(payload, bool):
        nums.append(float(payload))
    elif isinstance(payload, str):
        # We optionally extract from strings in payload if they are numerical representation, 
        # but typically payload data holds actual floats.
        pass
    return nums

def validate_advisory(synthesis_output: dict, computed_payload: dict, official_advisory: dict) -> GuardEvaluation:
    llm_verdict = synthesis_output.get('verdict_token')
    computed_verdict = computed_payload.get('verdict')
    explanation_text = synthesis_output.get('explanation_text', '')
    staleness_hours = computed_payload.get('staleness_hours', 0.0)

    fallback_notice = "\n\n[Automated synthesis rejected by safety guard. Displaying official marine advisory.]"
    fallback_text = official_advisory.get('text_en', 'No official advisory available.') + fallback_notice

    # Check 3: Staleness > 24 hours (NO_ADVISORY)
    if staleness_hours > 24:
        return GuardEvaluation(
            status="FAIL",
            reason="NO_ADVISORY",
            final_text=fallback_text,
            state="REJECTED"
        )

    # Check 1: Verdict Token Match
    if llm_verdict != computed_verdict:
        return GuardEvaluation(
            status="FAIL",
            reason="FAIL_VERDICT_CONTRADICTION",
            final_text=fallback_text,
            state="REJECTED"
        )

    # Check 2: Number Injection Validation
    text_nums = extract_numbers(explanation_text)
    payload_nums = get_all_payload_numbers(computed_payload)

    for tn in text_nums:
        # Match within ±0.1 tolerance
        match_found = any(abs(tn - pn) <= 0.1 for pn in payload_nums)
        if not match_found:
            return GuardEvaluation(
                status="FAIL",
                reason="FAIL_UNMATCHED_NUMERAL",
                final_text=fallback_text,
                state="REJECTED"
            )

    # All checks passed
    final_text = explanation_text
    
    # Check 3: Staleness Warning (>6 hours)
    if staleness_hours > 6:
        final_text += "\n[WARNING: Data is stale (>6 hours).]"

    return GuardEvaluation(
        status="PASS",
        reason="VALIDATED",
        final_text=final_text,
        state="RELEASED"
    )
