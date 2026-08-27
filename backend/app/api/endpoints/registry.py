from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.auth import require_token
from backend.app.db.session import get_db
from backend.app.models.source_registry import SourceRegistry
from backend.app.schemas.registry import RegistryCreate, RegistryResponse

router = APIRouter()

TIER_LABEL = {1: "Tier 1 · Indian / ISRO", 2: "Tier 2 · International", 3: "Tier 3 · Fallback"}


def _view(s: SourceRegistry) -> Dict[str, Any]:
    return {
        "source_id": s.source_id,
        "provider": s.provider,
        "country": s.country,
        "variables": s.variables,
        "spatial_coverage": s.spatial_coverage,
        "resolution_km": s.resolution_km,
        "access_method": s.access_method,
        "access_status": s.access_status,
        "priority_tier": s.priority_tier,
        "tier_label": TIER_LABEL.get(s.priority_tier, f"Tier {s.priority_tier}"),
        "provenance": s.provenance,
        "last_pull_ts": s.last_pull_ts,
    }


@router.get("/registry")
async def list_registry(db: AsyncSession = Depends(get_db)) -> Dict[str, Any]:
    """Full registry, tier order. Tier 1 (Indian/ISRO) always first (FR-22)."""
    result = await db.execute(
        select(SourceRegistry).order_by(SourceRegistry.priority_tier, SourceRegistry.provider))
    rows = [_view(s) for s in result.scalars().all()]
    return {
        "sources": rows,
        "summary": {
            "total": len(rows),
            "connected": sum(1 for r in rows if r["access_status"] == "CONNECTED"),
            "attempted": sum(1 for r in rows if r["access_status"] == "ATTEMPTED"),
            "substituted": sum(1 for r in rows if r["access_status"] == "SUBSTITUTED"),
            "tier_1": sum(1 for r in rows if r["priority_tier"] == 1),
        },
        "rule": ("R-8: an Indian/ISRO source is attempted before any non-Indian "
                 "substitute for every variable it covers."),
    }


@router.post("/registry", response_model=RegistryResponse, dependencies=[Depends(require_token)])
async def create_registry_entry(entry: RegistryCreate, db: AsyncSession = Depends(get_db)):
    """FR-08: adding a source changes discovery with no agent code change."""
    existing = await db.execute(
        select(SourceRegistry).filter(SourceRegistry.source_id == entry.source_id))
    if existing.scalars().first():
        raise HTTPException(status_code=409, detail="source_id already registered")
    db_entry = SourceRegistry(**entry.model_dump())
    db.add(db_entry)
    await db.commit()
    await db.refresh(db_entry)
    return db_entry


@router.delete("/registry/{source_id}", dependencies=[Depends(require_token)])
async def delete_registry_entry(source_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(SourceRegistry).filter(SourceRegistry.source_id == source_id))
    row = result.scalars().first()
    if not row:
        raise HTTPException(status_code=404, detail="Source not found")
    await db.delete(row)
    await db.commit()
    return {"status": "deleted", "source_id": source_id}


@router.get("/sources")
async def list_sources(db: AsyncSession = Depends(get_db)) -> Dict[str, Any]:
    """What the Sources panel renders: every source with provenance and status.

    Includes sources that did not connect. SRS 4.4 - a source that failed is
    shown as substituted, never silently dropped from the list.
    """
    return await list_registry(db)
