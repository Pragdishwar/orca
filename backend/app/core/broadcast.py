"""Renders one advisory into the four offline delivery formats (F-16, FR-39).

These are artefacts, not transmissions. No SMS gateway, IVR provider or VHF
transmitter is integrated; D-13 records who would own each channel and what it
would cost. Advisories and Sentinel alerts share this renderer, so an alert is
a different trigger for the same pipeline rather than a parallel one.
"""
from typing import Any, Dict, List

from backend.app.core import config_store

SMS_LIMIT = 160

VERDICT_SHORT = {
    "SAFE": "SAFE TO CROSS",
    "MARGINAL": "CAUTION",
    "DO_NOT_CROSS": "DO NOT CROSS",
}


def render_sms(adv: Dict[str, Any]) -> Dict[str, Any]:
    parts = [f"ORCA {VERDICT_SHORT[adv['verdict']]} {adv['inlet_name'].upper()}",
             f"{adv['hull_label']}",
             f"Hs {adv['hs_m']}m"]
    if adv.get("turn_back_label"):
        parts.append(f"turn back by {adv['turn_back_label']}")
    elif adv["verdict"] == "DO_NOT_CROSS":
        parts.append("no safe window today")
    text = ". ".join(parts) + "."
    return {
        "format": "sms",
        "content": text,
        "char_count": len(text),
        "limit": SMS_LIMIT,
        "over_limit": len(text) > SMS_LIMIT,
    }


def render_vhf(adv: Dict[str, Any]) -> Dict[str, Any]:
    lines = [
        "ALL STATIONS, ALL STATIONS. THIS IS THE MUTHALAPOZHI HARBOUR WATCH.",
        f"CROSSING ADVISORY FOR {adv['inlet_name'].upper()}, {adv['date']}.",
        f"FOR {adv['hull_label'].upper()} CLASS: {VERDICT_SHORT[adv['verdict']]}.",
        f"SIGNIFICANT WAVE HEIGHT {adv['hs_m']} METRES, PERIOD {adv['tp_s']} SECONDS, "
        f"TIDE {adv['tide_stage'].upper()}.",
    ]
    if adv.get("return_window"):
        lines.append(f"BAR PASSABLE {adv['return_window']['start_label']} TO "
                     f"{adv['return_window']['end_label']} HOURS.")
    if adv.get("turn_back_label"):
        lines.append(f"TURN BACK TIME {adv['turn_back_label']} HOURS.")
    lines.append("THIS IS AN ADVISORY FOR PLANNING ASHORE. IT IS NOT A NAVIGATION "
                 "INSTRUCTION. OUT.")
    return {
        "format": "vhf",
        "content": "\n".join(lines),
        # M-05 is a pre-rendered tone placeholder, not speech. Said plainly so
        # nobody mistakes the demo for working text-to-speech.
        "audio_url": "/static/audio/vhf_alert_en.wav",
        "audio_is_placeholder": True,
    }


def render_slip(adv: Dict[str, Any]) -> Dict[str, Any]:
    rw = adv.get("return_window")
    lines = [
        "ORCA CROSSING SLIP",
        "=" * 32,
        f"INLET   : {adv['inlet_name']}",
        f"DATE    : {adv['date']}",
        f"HULL    : {adv['hull_label']}",
        "",
        f"VERDICT : {VERDICT_SHORT[adv['verdict']]}",
        "",
        f"WAVE    : {adv['hs_m']} m at {adv['tp_s']} s",
        f"TIDE    : {adv['tide_stage']}",
        f"INDEX   : {adv['index_value']} (unsafe at {adv['index_unsafe']})",
        f"WINDOW  : {rw['start_label']}-{rw['end_label']}" if rw else "WINDOW  : none today",
        f"TURN BACK BY: {adv['turn_back_label']}" if adv.get("turn_back_label")
        else "TURN BACK BY: n/a",
        "=" * 32,
        "Planning guidance only. Not for navigation.",
        "Data: SYNTHETIC_STRUCTURED. Prototype.",
    ]
    return {"format": "slip", "content": "\n".join(lines), "page_size": "A5"}


def render_board(adv: Dict[str, Any], hull_comparison: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Landing-centre board: every hull class side by side (FR-39)."""
    return {
        "format": "board",
        "headline": VERDICT_SHORT[adv["verdict"]],
        "inlet": adv["inlet_name"],
        "date": adv["date"],
        "buckets": [
            {"hull_label": h["hull_label"], "verdict": h["verdict"],
             "short": VERDICT_SHORT[h["verdict"]], "index_value": h["index_value"]}
            for h in hull_comparison
        ],
        "footer": f"Index {adv['index_value']} · Hs {adv['hs_m']} m · tide {adv['tide_stage']}",
    }


def render_all(adv: Dict[str, Any], hull_comparison: List[Dict[str, Any]]) -> Dict[str, Any]:
    cfg = config_store.channels()
    return {
        "sms": render_sms(adv),
        "vhf": render_vhf(adv),
        "slip": render_slip(adv),
        "board": render_board(adv, hull_comparison),
        "channels": cfg["rows"],
        "monthly_infra_inr_10_centres": cfg["monthly_infra_inr_10_centres"],
        "notice": ("Rendered, not transmitted. No SMS gateway, IVR or VHF transmitter "
                   "is integrated in this prototype."),
    }
