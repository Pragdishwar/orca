from typing import List
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.app.schemas.boat import BoatCreate, BoatResponse, BoatUpdate
from backend.app.core.auth import require_token
from backend.app.db.session import get_db
from backend.app.models.boat import Boat

router = APIRouter()

@router.post("", response_model=BoatResponse, dependencies=[Depends(require_token)])
async def create_boat(boat: BoatCreate, db: AsyncSession = Depends(get_db)):
    db_boat = Boat(**boat.model_dump())
    db.add(db_boat)
    await db.commit()
    await db.refresh(db_boat)
    return db_boat

@router.get("", response_model=List[BoatResponse])
async def list_boats(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Boat))
    return result.scalars().all()

@router.get("/{boat_id}", response_model=BoatResponse)
async def get_boat(boat_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Boat).filter(Boat.boat_id == boat_id))
    boat = result.scalars().first()
    if not boat:
        raise HTTPException(status_code=404, detail="Boat not found")
    return boat

@router.put("/{boat_id}", response_model=BoatResponse, dependencies=[Depends(require_token)])
async def update_boat(boat_id: str, boat_update: BoatUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Boat).filter(Boat.boat_id == boat_id))
    boat = result.scalars().first()
    if not boat:
        raise HTTPException(status_code=404, detail="Boat not found")
    
    update_data = boat_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(boat, key, value)
        
    await db.commit()
    await db.refresh(boat)
    return boat

@router.delete("/{boat_id}", dependencies=[Depends(require_token)])
async def delete_boat(boat_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Boat).filter(Boat.boat_id == boat_id))
    boat = result.scalars().first()
    if not boat:
        raise HTTPException(status_code=404, detail="Boat not found")
    
    await db.delete(boat)
    await db.commit()
    return {"status": "success"}
