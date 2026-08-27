from typing import Any, Dict, List

from fastapi import APIRouter

from backend.app.core import config_store
from backend.app.core.auth import officers

router = APIRouter()


@router.get("")
async def list_personas() -> Dict[str, List[Dict[str, Any]]]:
    """FR-27/FR-28: the five personas, driven entirely by D-16 config.

    Changing a persona's layers, framing or suggested queries is a config edit.
    The agent stack does not branch on persona at all.
    """
    return {"personas": config_store.personas()}


@router.post("/reload")
async def reload_config() -> Dict[str, str]:
    """Re-read the config files without a restart, for a live edit demo."""
    config_store.reload_all()
    return {"status": "reloaded"}


@router.get("/officers")
async def list_officers() -> Dict[str, Any]:
    """Who may be recorded as releasing an advisory (SRS 7.4).

    An authorisation roster, not authentication - it constrains the audit field
    to real, named posts instead of free text.
    """
    return {
        "officers": officers(),
        "note": ("Release is gated on a shared demo token plus a roster entry. This "
                 "prototype has no user accounts, so it records who is accountable - "
                 "it does not verify who is at the keyboard."),
    }
