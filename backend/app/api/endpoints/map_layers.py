"""GeoJSON for the map pane's seven toggleable layers (FR-20).

Served from the backend rather than bundled in the client so the same
geometry drives the geofence predicate and the drawn polygon - there is no
second copy of the zones to drift out of sync.
"""
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Query

from backend.app.core.dataset import INLET
from backend.app.core.geo import circle_ring
from backend.app.core.seed_data import (
    NAMED_GROUNDS,
    ZONES,
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
) -> Dict[str, Any]:
    return {
        "inlet": inlet_feature(),
        "hazard_corridor": _hazard_corridor(verdict, index_value),
        "pfz": _pfz_layer(user_lat, user_lon),
        "geofences": _zone_layer(),
        "grounds": {"type": "FeatureCollection", "features": ground_rings()},
        "coverage_line": _coverage_line(),
        "centre": [INLET["lon"], INLET["lat"]],
        "provenance": "SYNTHETIC",
    }


def _hazard_corridor(verdict: Optional[str], index_value: float) -> Dict[str, Any]:
    """The approach corridor across the bar, coloured by the active verdict."""
    import math
    lat, lon = INLET["lat"], INLET["lon"]
    bearing = math.radians(INLET["channel_bearing_deg"])
    perp = bearing + math.pi / 2
    reach_km, half_width_km = 4.0, 0.55

    def offset(d_along: float, d_across: float) -> List[float]:
        dlat = ((d_along / 110.574) * math.cos(bearing)
                + (d_across / 110.574) * math.cos(perp))
        dlon = ((d_along / (111.320 * math.cos(math.radians(lat)))) * math.sin(bearing)
                + (d_across / (111.320 * math.cos(math.radians(lat)))) * math.sin(perp))
        return [round(lon + dlon, 6), round(lat + dlat, 6)]

    ring = [offset(0, -half_width_km), offset(reach_km, -half_width_km * 2.2),
            offset(reach_km, half_width_km * 2.2), offset(0, half_width_km)]
    ring.append(ring[0])

    colour = {"SAFE": "#059669", "MARGINAL": "#d97706",
              "DO_NOT_CROSS": "#dc2626"}.get(verdict or "", "#64748b")

    return {"type": "FeatureCollection", "features": [{
        "type": "Feature",
        "properties": {"kind": "hazard_corridor", "verdict": verdict,
                       "index_value": index_value, "colour": colour,
                       "bearing_deg": INLET["channel_bearing_deg"]},
        "geometry": {"type": "Polygon", "coordinates": [ring]},
    }]}


def _pfz_layer(user_lat: Optional[float] = None, user_lon: Optional[float] = None) -> Dict[str, Any]:
    return {"type": "FeatureCollection", "features": [{
        "type": "Feature",
        "properties": {"pfz_id": p["pfz_id"], "depth_m": p["depth_m"],
                       "confidence": p["confidence"], "provenance": p["provenance"]},
        "geometry": {"type": "Point", "coordinates": [p["lon"], p["lat"]]},
    } for p in pfz_points(user_lat, user_lon)]}


def _zone_layer() -> Dict[str, Any]:
    return {"type": "FeatureCollection", "features": [{
        "type": "Feature",
        "properties": {"zone_id": z["zone_id"], "name": z["name"], "type": z["type"],
                       "buffer_km": z["buffer_km"], "provenance": z["provenance"],
                       "colour": ZONE_COLOURS.get(z["type"], "#64748b")},
        "geometry": z["geojson"],
    } for z in ZONES]}


def _coverage_line() -> Dict[str, Any]:
    """Where mobile coverage ends - the reason offline compile exists at all."""
    import math
    features = []
    for km, label in ((15.0, "Approximate mobile coverage limit"),):
        ring = circle_ring(INLET["lat"], INLET["lon"], km, points=64)
        features.append({
            "type": "Feature",
            "properties": {"kind": "coverage_line", "label": label, "radius_km": km,
                           "note": ("Beyond this line a live interface is unavailable. "
                                    "Advisories must already be aboard."),
                           "provenance": "SYNTHETIC"},
            "geometry": {"type": "LineString", "coordinates": ring},
        })
    return {"type": "FeatureCollection", "features": features}
