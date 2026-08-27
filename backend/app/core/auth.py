"""Write-endpoint protection and release authorisation (SRS 7.4).

Two separate things, deliberately not conflated:

* `require_token` gates every state-changing endpoint on a shared demo token.
  This is NOT authentication. A static token shipped to a browser is readable
  by anyone who opens devtools; it stops accidental and casual writes, nothing
  more.

* `validate_officer` checks the name recorded against a release is one of the
  roster entries, so the audit field cannot be filled with arbitrary text. It
  establishes who is *recorded* as accountable; it does not prove the person at
  the keyboard is that officer.

Real role-based access control needs a server-side identity provider, per-user
credentials and signed sessions. None of that is in this prototype, and the
Coverage tab says so rather than implying otherwise.
"""
import json
import os
from functools import lru_cache
from typing import Any, Dict, List

from fastapi import Header, HTTPException

CONFIG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                          "config")

DEMO_TOKEN = os.getenv("ORCA_DEMO_TOKEN", "orca-demo-token")
# Set ORCA_REQUIRE_TOKEN=0 to run the API open, e.g. for scripted testing.
REQUIRE_TOKEN = os.getenv("ORCA_REQUIRE_TOKEN", "1") != "0"


@lru_cache(maxsize=1)
def officers() -> List[Dict[str, Any]]:
    with open(os.path.join(CONFIG_DIR, "officers.json"), "r", encoding="utf-8") as fh:
        return json.load(fh)["officers"]


async def require_token(x_orca_token: str = Header(default="")) -> None:
    """Dependency for every write endpoint."""
    if not REQUIRE_TOKEN:
        return
    if x_orca_token != DEMO_TOKEN:
        raise HTTPException(
            status_code=401,
            detail="Missing or invalid X-ORCA-Token header. Write endpoints are gated "
                   "(SRS 7.4).",
        )


def validate_officer(name: str) -> Dict[str, Any]:
    """Resolve a release to a roster entry, by officer_id or exact name."""
    candidate = (name or "").strip()
    if not candidate:
        raise HTTPException(status_code=400,
                            detail="officer_name is required to release (R-4)")
    for o in officers():
        if candidate in (o["officer_id"], o["name"]):
            return o
    known = ", ".join(f"{o['officer_id']} ({o['name']})" for o in officers())
    raise HTTPException(
        status_code=403,
        detail=f"'{candidate}' is not on the authorised release roster. "
               f"Permitted: {known}",
    )
