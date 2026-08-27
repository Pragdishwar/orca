from typing import Any, Dict

from fastapi import APIRouter

from backend.app.core import config_store

router = APIRouter()


@router.get("")
async def get_coverage() -> Dict[str, Any]:
    """PS requirement coverage matrix (FR-44), read from D-12 config."""
    rows = config_store.coverage_rows()
    built = sum(1 for r in rows if r["status"] == "BUILT")
    return {
        "rows": rows,
        "summary": {"built": built, "mockup": len(rows) - built, "total": len(rows)},
    }
