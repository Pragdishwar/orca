import pytest
from backend.app.core.guard import validate_advisory, GuardEvaluation

# Official Advisory Fixture
OFFICIAL_ADVISORY = {
    "text_en": "Official INCOIS Advisory: Proceed with caution."
}

# The M-03 Dataset Test Matrix (20 Cases)
# Structure: (synthesis_verdict, explanation_text, computed_verdict, payload_metrics, staleness, expected_status, expected_reason)
M_03_DATASET = [
    # ---- 10 PASS CASES ----
    ("SAFE", "Safe to cross. Waves are at 1.5m.", "SAFE", {"hs": 1.5}, 2, "PASS", "VALIDATED"),
    ("SAFE", "Safe. Max wave is 2.0m and period 8s.", "SAFE", {"hs": 2.0, "tp": 8.0}, 1, "PASS", "VALIDATED"),
    ("MARGINAL", "Marginal conditions. Hazard index 0.6.", "MARGINAL", {"index": 0.6}, 4, "PASS", "VALIDATED"),
    ("DO_NOT_CROSS", "Do not cross! Waves 4.0 m.", "DO_NOT_CROSS", {"hs": 4.0}, 5, "PASS", "VALIDATED"),
    ("SAFE", "All good.", "SAFE", {"hs": 1.0}, 0, "PASS", "VALIDATED"),
    ("MARGINAL", "Waves are 2.5m.", "MARGINAL", {"wave": {"hs": 2.53}}, 0, "PASS", "VALIDATED"), # Tests ±0.1 rounding
    ("SAFE", "Wave 1.0 m, speed 10 knots.", "SAFE", {"hs": 1.0, "spd": 10}, 1, "PASS", "VALIDATED"),
    ("DO_NOT_CROSS", "Dangerous 3.5m swell.", "DO_NOT_CROSS", {"swell": 3.55}, 1, "PASS", "VALIDATED"),
    ("SAFE", "Clear at 0.5m.", "SAFE", {"hs": 0.5}, 5, "PASS", "VALIDATED"),
    ("MARGINAL", "Watch out for 1.8m waves.", "MARGINAL", {"hs": 1.75}, 1, "PASS", "VALIDATED"),
    
    # ---- 8 DELIBERATE CONTRADICTION CASES ----
    # 1. Verdict Contradiction (LLM hallucinates safe on unsafe data)
    ("SAFE", "Looks fine, go ahead.", "DO_NOT_CROSS", {"hs": 4.5}, 1, "FAIL", "FAIL_VERDICT_CONTRADICTION"),
    # 2. Verdict Contradiction
    ("MARGINAL", "Maybe risky.", "SAFE", {"hs": 1.0}, 1, "FAIL", "FAIL_VERDICT_CONTRADICTION"),
    # 3. Unmatched numeral (Hallucinated wave height)
    ("SAFE", "Waves are 2.5m.", "SAFE", {"hs": 1.0}, 1, "FAIL", "FAIL_UNMATCHED_NUMERAL"),
    # 4. Unmatched numeral (Invented distance)
    ("MARGINAL", "Marginal because shore is 50km away.", "MARGINAL", {"dist": 20}, 1, "FAIL", "FAIL_UNMATCHED_NUMERAL"),
    # 5. Both Mismatch & Verdict (Verdict takes precedence in code logic)
    ("SAFE", "Waves 1.0m", "DO_NOT_CROSS", {"hs": 4.0}, 1, "FAIL", "FAIL_VERDICT_CONTRADICTION"),
    # 6. Unmatched numeral (LLM hallucinates a random number in text)
    ("SAFE", "There are 5 boats.", "SAFE", {"boats_nearby": 2}, 1, "FAIL", "FAIL_UNMATCHED_NUMERAL"),
    # 7. Exact mismatch on decimals outside 0.1 tolerance (2.5 vs 2.7)
    ("MARGINAL", "Waves are 2.5m.", "MARGINAL", {"hs": 2.7}, 1, "FAIL", "FAIL_UNMATCHED_NUMERAL"),
    # 8. Unmatched numeral (Inventing percentages)
    ("SAFE", "100% safe.", "SAFE", {"hs": 1.0}, 1, "FAIL", "FAIL_UNMATCHED_NUMERAL"),

    # ---- 2 STALENESS CASES ----
    # 1. > 6 Hours (Should PASS but append STALE warning)
    ("SAFE", "Safe. Waves 1.5m.", "SAFE", {"hs": 1.5}, 10, "PASS", "VALIDATED"),
    # 2. > 24 Hours (Should FAIL with NO_ADVISORY)
    ("SAFE", "Safe. Waves 1.5m.", "SAFE", {"hs": 1.5}, 26, "FAIL", "NO_ADVISORY"),
]

@pytest.mark.parametrize(
    "syn_verdict, syn_text, comp_verdict, comp_payload, staleness, expected_status, expected_reason",
    M_03_DATASET
)
def test_guard_m03_dataset(syn_verdict, syn_text, comp_verdict, comp_payload, staleness, expected_status, expected_reason):
    
    synthesis_output = {
        "verdict_token": syn_verdict,
        "explanation_text": syn_text
    }
    
    computed_payload = {
        "verdict": comp_verdict,
        "staleness_hours": staleness,
        **comp_payload
    }
    
    result = validate_advisory(synthesis_output, computed_payload, OFFICIAL_ADVISORY)
    
    assert result.status == expected_status
    assert result.reason == expected_reason
    
    if expected_status == "FAIL":
        assert result.state == "REJECTED"
        assert "Automated synthesis rejected by safety guard" in result.final_text
        assert OFFICIAL_ADVISORY["text_en"] in result.final_text
    else:
        assert result.state == "RELEASED"
        # Check staleness warning
        if staleness > 6 and expected_status == "PASS":
            assert "WARNING: Data is stale (>6 hours)" in result.final_text
