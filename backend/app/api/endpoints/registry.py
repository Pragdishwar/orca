from typing import List
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.app.schemas.registry import RegistryCreate, RegistryResponse
from backend.app.db.session import get_db
from backend.app.models.source_registry import SourceRegistry

router = APIRouter()

@router.post("/registry", response_model=RegistryResponse)
async def create_registry_entry(entry: RegistryCreate, db: AsyncSession = Depends(get_db)):
    db_entry = SourceRegistry(**entry.model_dump())
    db.add(db_entry)
    await db.commit()
    await db.refresh(db_entry)
    return db_entry

@router.get("/registry", response_model=List[RegistryResponse])
async def list_registry_entries(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(SourceRegistry))
    return result.scalars().all()

@router.get("/sources", response_model=List[RegistryResponse])
async def list_sources(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(SourceRegistry).filter(SourceRegistry.access_status == "active"))
    return result.scalars().all()
