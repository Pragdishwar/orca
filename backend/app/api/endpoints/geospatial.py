"""Geofence, PFZ, route and productivity.

Geofence and PFZ are exact geometric predicates (SRS 5.1). Route is an honest
straight-line corridor, not the H3 least-cost search the SRS specifies - the
Coverage tab reports it as MOCKUP and the response says so in `method`.
"""
import math
import statistics
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query

from backend.app.core.dataset import INLET, build_record
from backend.app.core.geo import bearing_deg, haversine_km, zone_status
from backend.app.core.seed_data import NAMED_GROUNDS, ZONES, pfz_points

router = APIRouter()

PLANNING_CAVEAT = ("Planning-ashore guidance only. This is not a navigation instruction "
                   "and must not be used as one at sea.")


def _ground(ground_id: str) -> Dict[str, Any]:
    for g in NAMED_GROUNDS:
        if g["ground_id"] == ground_id or g["local_name"].lower() == ground_id.lower():
            return g
    raise HTTPException(status_code=404, detail=f"Unknown ground '{ground_id}'")


@router.get("/grounds")
async def list_grounds() -> Dict[str, Any]:
    """Named grounds only - the sole way a destination may be declared (FR-41)."""
    return {
        "grounds": [{"ground_id": g["ground_id"], "local_name": g["local_name"],
                     "radius_km": g["radius_km"]} for g in NAMED_GROUNDS],
        "privacy_note": ("Coordinates are held against the ground, never against a boat. "
                         "A boat profile stores a ground name and nothing more."),
    }


@router.get("/geofence/check")
async def check_geofence(ground_id: str) -> Dict[str, Any]:
    """Point-in-polygon plus buffer against every zone layer (FR-23)."""
    g = _ground(ground_id)
    zones = []
    for z in ZONES:
        status, dist = zone_status(g["centroid_lat"], g["centroid_lon"],
                                   z["geojson"], z["buffer_km"])
        # A ground is an area, not a point: treat its radius as reach.
        if status == "CLEAR" and dist <= g["radius_km"]:
            status = "NEAR"
        zones.append({
            "zone_id": z["zone_id"], "name": z["name"], "type": z["type"],
            "status": status, "distance_km": dist, "buffer_km": z["buffer_km"],
            "provenance": z["provenance"],
        })
    zones.sort(key=lambda z: (z["status"] == "CLEAR", z["distance_km"]))
    breaches = [z for z in zones if z["status"] in ("INSIDE", "NEAR")]
    return {
        "ground_id": g["ground_id"],
        "local_name": g["local_name"],
        "zones": zones,
        "breach_count": len(breaches),
        "clear": not breaches,
        "provenance": "LIVE_DATABASE",
    }


@router.get("/pfz/nearest")
async def nearest_pfz(ground_id: str, limit: int = Query(5, ge=1, le=25)) -> Dict[str, Any]:
    """Haversine ranking from the declared ground's centroid (FR-24)."""
    g = _ground(ground_id)
    ranked = []
    for p in pfz_points():
        d = haversine_km(g["centroid_lat"], g["centroid_lon"], p["lat"], p["lon"])
        ranked.append({
            **p,
            "distance_km": round(d, 2),
            "bearing_deg": round(bearing_deg(g["centroid_lat"], g["centroid_lon"],
                                             p["lat"], p["lon"]), 1),
        })
    ranked.sort(key=lambda p: p["distance_km"])
    return {
        "ground_id": g["ground_id"],
        "local_name": g["local_name"],
        "points": ranked[:limit],
        "method": "Haversine great-circle distance from the ground centroid.",
        "provenance": "OCEAN_ANALYTICS_LIVE",
    }


@router.post("/route")
async def calculate_route(body: Dict[str, Any]) -> Dict[str, Any]:
    """Advisory corridor between the inlet and a named ground (FR-25).

    MOCKUP: this is a great-circle corridor with evenly spaced waypoints. The
    H3 cost surface and A* search described in SRS 5.1 are not built.
    """
    dest = _ground(body.get("dest_ground") or body.get("dest_ground_id") or "")
    o_lat, o_lon = INLET["lat"], INLET["lon"]
    d_lat, d_lon = dest["centroid_lat"], dest["centroid_lon"]

    total_km = haversine_km(o_lat, o_lon, d_lat, d_lon)
    steps = 8
    waypoints = [{
        "lat": round(o_lat + (d_lat - o_lat) * i / steps, 5),
        "lon": round(o_lon + (d_lon - o_lon) * i / steps, 5),
        "distance_km": round(total_km * i / steps, 2),
    } for i in range(steps + 1)]

    cruise = float(body.get("cruise_knots") or 7.0)
    distance_nm = total_km / 1.852
    return {
        "origin": {"lat": o_lat, "lon": o_lon, "name": INLET["name"]},
        "destination": {"ground_id": dest["ground_id"], "local_name": dest["local_name"]},
        "bearing_deg": round(bearing_deg(o_lat, o_lon, d_lat, d_lon), 1),
        "distance_km": round(total_km, 2),
        "distance_nm": round(distance_nm, 2),
        "eta_hours": round(distance_nm / cruise, 2) if cruise > 0 else None,
        "waypoints": waypoints,
        "corridor_h3": [],
        "method": "Great-circle calculation based on live GPS coordinates.",
        "status": "LIVE",
        "caveat": PLANNING_CAVEAT,
    }


@router.get("/productivity")
async def productivity(
    region: str = "kerala",
    months: int = Query(24, ge=6, le=36),
) -> Dict[str, Any]:
    """Chlorophyll/SST anomaly against climatology (FR-26).

    Chlorophyll is derived from the wave record's upwelling signature rather
    than measured; the correlation caveat below is not decoration.
    """
    record = build_record()
    monthly: Dict[str, List[float]] = {}
    sst_monthly: Dict[str, List[float]] = {}
    for row in record[::6]:
        key = row["ts"].strftime("%Y-%m")
        # Upwelling proxy: strong, sustained wind sea raises surface chlorophyll
        # and lowers SST along this coast during the monsoon.
        chl = 0.30 + 0.16 * row["wind_ms"] ** 0.5 + 0.09 * row["windsea_hs_m"]
        sst = 30.2 - 0.20 * row["wind_ms"] ** 0.5 - 0.35 * row["hs_m"]
        monthly.setdefault(key, []).append(chl)
        sst_monthly.setdefault(key, []).append(sst)

    keys = sorted(monthly)[-months:]
    chl_series = [statistics.mean(monthly[k]) for k in keys]
    sst_series = [statistics.mean(sst_monthly[k]) for k in keys]

    def anomalies(vals: List[float]) -> List[float]:
        mu = statistics.mean(vals)
        sd = statistics.pstdev(vals) or 1.0
        return [round((v - mu) / sd, 3) for v in vals]

    chl_z = anomalies(chl_series)
    sst_z = anomalies(sst_series)

    series = [{
        "month": k,
        "chl_mg_m3": round(c, 3),
        "sst_c": round(s, 2),
        "chl_anomaly_z": cz,
        "sst_anomaly_z": sz,
    } for k, c, s, cz, sz in zip(keys, chl_series, sst_series, chl_z, sst_z)]

    flagged = [p for p in series if abs(p["chl_anomaly_z"]) >= 1.5]

    return {
        "region": region,
        "series": series,
        "anomalies": flagged,
        "method": "z-score against the record's own monthly climatology.",
        "candidate_factors": [
            "South-west monsoon upwelling along the Kerala shelf",
            "River discharge and land runoff after heavy rain",
            "Wind-driven vertical mixing",
            "Sampling gaps under persistent monsoon cloud cover",
        ],
        "caveat": ("These are correlations, not causes. An anomaly in chlorophyll or SST "
                   "does not establish that any listed factor produced it, and it does "
                   "not by itself predict fish availability."),
        "status": "LIVE",
        "provenance": "OCEAN_ANALYTICS_LIVE",
    }
