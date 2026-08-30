"""GeoJSON for the map pane's seven toggleable layers (FR-20).

Served from the backend rather than bundled in the client so the same
geometry drives the geofence predicate and the drawn polygon - there is no
second copy of the zones to drift out of sync.
"""
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.db.session import get_db

from backend.app.core.dataset import INLET
from backend.app.core.geo import circle_ring
from backend.app.core.seed_data import (
    named_grounds,
    geofence_zones,
    get_inlet,
    ground_rings,
    inlet_feature,
    pfz_points,
)

router = APIRouter()

ZONE_COLOURS = {
    "IMBL": "#dc2626",
    "MPA": "#059669",
    "SENSITIVE": "#d97706",
    "RESTRICTED": "#7c3aed",
}


@router.get("")
async def get_layers(
    verdict: Optional[str] = Query(None, description="Colours the hazard corridor."),
    index_value: float = Query(0.0, ge=0.0, le=1.0),
    user_lat: Optional[float] = Query(None),
    user_lon: Optional[float] = Query(None),
    boat_id: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    return {
        "inlet": inlet_feature(user_lat, user_lon),
        "hazard_corridor": _hazard_corridor(verdict, index_value, user_lat, user_lon),
        "pfz": await _pfz_layer(user_lat, user_lon),
        "geofences": await _zone_layer(),
        "grounds": {"type": "FeatureCollection", "features": ground_rings()},
        "coverage_line": await _coverage_line(user_lat, user_lon, boat_id, db),
        "centre": [
            get_inlet(user_lat, user_lon)["lon"],
            get_inlet(user_lat, user_lon)["lat"]
        ],
        "provenance": "REALTIME",
    }


def _hazard_corridor(verdict: Optional[str], index_value: float, user_lat: float = None, user_lon: float = None) -> Dict[str, Any]:
    """The approach corridor across the bar, coloured by the active verdict."""
    import math
    inlet = get_inlet(user_lat, user_lon)
    lat, lon = inlet["lat"], inlet["lon"]
    bearing = math.radians(inlet["channel_bearing_deg"])
    reach_km = 3.0
    dlat = (reach_km / 110.574) * math.cos(bearing)
    dlon = (reach_km / (111.320 * math.cos(math.radians(lat)))) * math.sin(bearing)

    polygon = [
        [lon - 0.002, lat - 0.002],
        [lon + 0.002, lat + 0.002],
        [lon + dlon + 0.002, lat + dlat + 0.002],
        [lon + dlon - 0.002, lat + dlat - 0.002],
        [lon - 0.002, lat - 0.002],
    ]
    return {
        "type": "FeatureCollection",
        "features": [{
            "type": "Feature",
            "properties": {"kind": "hazard_corridor", "verdict": verdict or "CLEAR",
                           "index_value": index_value, "provenance": "ORCA_PHYSICS"},
            "geometry": {"type": "Polygon", "coordinates": [polygon]},
        }],
    }


async def _pfz_layer(user_lat: float = None, user_lon: float = None) -> Dict[str, Any]:
    pts = await pfz_points(user_lat, user_lon)
    return {"type": "FeatureCollection", "features": [{
        "type": "Feature",
        "properties": {"kind": "pfz", "pfz_id": p["pfz_id"], "depth_m": p["depth_m"],
                       "confidence": p.get("confidence"), "provenance": p.get("provenance", "OCEAN_ANALYTICS_LIVE")},
        "geometry": {"type": "Point", "coordinates": [p["lon"], p["lat"]]},
    } for p in pts]}


async def _zone_layer() -> Dict[str, Any]:
    from backend.app.db.supabase import supabase
    zones = geofence_zones()
    if supabase:
        try:
            res = supabase.table("zones").select("*").execute()
            if res.data:
                zones = res.data
        except Exception as e:
            print(f"Supabase zones error: {e}")

    return {"type": "FeatureCollection", "features": [{
        "type": "Feature",
        "properties": {"kind": "geofence", "zone_id": z.get("zone_id"), "name": z.get("name"),
                       "buffer_km": z.get("buffer_km"), "provenance": z.get("provenance", "OCEAN_ANALYTICS_LIVE"),
                       "colour": z.get("colour", ZONE_COLOURS.get(str(z.get("type")).upper(), "#64748b"))},
        "geometry": z.get("geojson") or z.get("geometry"),
    } for z in zones]}


async def _coverage_line(user_lat: float = None, user_lon: float = None, boat_id: str = None, db: AsyncSession = None) -> Dict[str, Any]:
    """Where mobile coverage ends - the reason offline compile exists at all."""
    features = []
    
    # Calculate from the boat's home harbour if known, otherwise fallback to the nearest inlet/user location
    target_lat, target_lon = INLET["lat"], INLET["lon"]
    if boat_id and db:
        from backend.app.models.boat import Boat
        boat_res = await db.execute(select(Boat).filter(Boat.boat_id == boat_id))
        boat = boat_res.scalars().first()
        if boat:
            for g in named_grounds():
                if g["local_name"].lower() == boat.home_harbour.lower() or g["ground_id"] == boat.home_harbour:
                    target_lat = g["centroid_lat"]
                    target_lon = g["centroid_lon"]
                    break
    elif user_lat is not None and user_lon is not None:
        target_lat = user_lat
        target_lon = user_lon
        
    for km, label in ((15.0, "Approximate mobile coverage limit"),):
        ring = circle_ring(target_lat, target_lon, km, points=64)
        features.append({
            "type": "Feature",
            "properties": {"kind": "coverage_line", "label": label, "radius_km": km,
                           "note": ("Beyond this line a live interface is unavailable. "
                                    "Advisories must already be aboard."),
                           "provenance": "SYNTHETIC"},
            "geometry": {"type": "LineString", "coordinates": ring},
        })
    return {"type": "FeatureCollection", "features": features}
