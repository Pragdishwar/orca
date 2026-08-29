"""Answering the non-crossing intents.

The planner already classifies a query as nearest-PFZ, geofence check, route or
productivity; without this module the graph computed a crossing verdict
regardless and answered the wrong question.

Every number returned here comes from a deterministic geometric routine
(haversine, point-in-polygon, great-circle) - none is generated text - so the
figures quoted in the answer are the figures that were computed.
"""
from typing import Any, Dict, List, Optional

from backend.app.core.dataset import INLET
from backend.app.core.geo import bearing_deg, haversine_km, zone_status
from backend.app.core.seed_data import NAMED_GROUNDS, ZONES, pfz_points

DEFAULT_GROUND = "G-MUTH-NEAR"


def resolve_ground(ground_id: str) -> Dict[str, Any]:
    for g in NAMED_GROUNDS:
        if g["ground_id"] == ground_id or g["local_name"].lower() == str(ground_id).lower():
            return g
    for g in NAMED_GROUNDS:
        if g["ground_id"] == DEFAULT_GROUND:
            return g
    return NAMED_GROUNDS[0]


def nearest_pfz(ground_id: str, limit: int = 3) -> Dict[str, Any]:
    g = resolve_ground(ground_id)
    ranked = []
    for p in pfz_points():
        d = haversine_km(g["centroid_lat"], g["centroid_lon"], p["lat"], p["lon"])
        ranked.append({
            "pfz_id": p["pfz_id"],
            "lat": p["lat"], "lon": p["lon"],
            "depth_m": p["depth_m"], "confidence": p["confidence"],
            "distance_km": round(d, 2),
            "bearing_deg": round(bearing_deg(g["centroid_lat"], g["centroid_lon"],
                                             p["lat"], p["lon"]), 1),
        })
    ranked.sort(key=lambda p: p["distance_km"])
    top = ranked[:limit]

    if not top:
        return {"kind": "nearest_pfz", "answer": "No PFZ advisory points are on file.",
                "points": [], "ground": g["local_name"]}

    first = top[0]
    others = ", ".join(f"{p['pfz_id']} at {p['distance_km']} km" for p in top[1:])
    answer = (
        f"The nearest potential fishing zone to {g['local_name']} is {first['pfz_id']}, "
        f"{first['distance_km']} km away on a bearing of {first['bearing_deg']} degrees, "
        f"in {first['depth_m']} m of water."
    )
    if others:
        answer += f" Next closest: {others}."
    answer += (" Distances are straight-line from the declared ground, not sailing "
               "distance, and the PFZ points are synthetic.")
    return {"kind": "nearest_pfz", "answer": answer, "points": top,
            "ground": g["local_name"], "ground_id": g["ground_id"],
            "method": "Haversine ranking from the ground centroid.",
            "provenance": "SYNTHETIC"}


def geofence_check(ground_id: str) -> Dict[str, Any]:
    g = resolve_ground(ground_id)
    zones = []
    for z in ZONES:
        status, dist = zone_status(g["centroid_lat"], g["centroid_lon"],
                                   z["geojson"], z["buffer_km"])
        if status == "CLEAR" and dist <= g["radius_km"]:
            status = "NEAR"
        zones.append({"zone_id": z["zone_id"], "name": z["name"], "type": z["type"],
                      "status": status, "distance_km": dist})
    zones.sort(key=lambda z: (z["status"] == "CLEAR", z["distance_km"]))
    breaches = [z for z in zones if z["status"] in ("INSIDE", "NEAR")]

    if breaches:
        parts = [f"{z['name']} ({z['type']}, {z['status'].lower()}, {z['distance_km']} km)"
                 for z in breaches]
        answer = (f"{g['local_name']} touches {len(breaches)} restricted or protected "
                  f"area(s) before departure: {'; '.join(parts)}.")
    else:
        answer = (f"{g['local_name']} is clear of every IMBL, protected, sensitive and "
                  f"restricted zone on file. Nearest is {zones[0]['name']} at "
                  f"{zones[0]['distance_km']} km.")
    answer += " Zone polygons are synthetic and flagged as such."
    return {"kind": "geofence_check", "answer": answer, "zones": zones,
            "ground": g["local_name"], "ground_id": g["ground_id"],
            "breach_count": len(breaches), "provenance": "SYNTHETIC"}


def route_advisory(ground_id: str, cruise_knots: float) -> Dict[str, Any]:
    g = resolve_ground(ground_id if ground_id else "G-QUILON")
    total_km = haversine_km(INLET["lat"], INLET["lon"],
                            g["centroid_lat"], g["centroid_lon"])
    nm = total_km / 1.852
    brg = bearing_deg(INLET["lat"], INLET["lon"], g["centroid_lat"], g["centroid_lon"])
    eta = nm / cruise_knots if cruise_knots > 0 else None
    answer = (
        f"From {INLET['name']} to {g['local_name']} is {round(nm, 1)} nautical miles on a "
        f"bearing of {round(brg, 1)} degrees"
    )
    answer += (f", about {round(eta, 1)} hours at {cruise_knots} knots."
               if eta else ".")
    answer += (" This is a great-circle corridor for planning ashore, not a least-cost "
               "route and not a navigation instruction.")
    return {"kind": "route_advisory", "answer": answer, "ground": g["local_name"],
            "ground_id": g["ground_id"], "distance_nm": round(nm, 2),
            "bearing_deg": round(brg, 1),
            "eta_hours": round(eta, 2) if eta else None,
            "status": "MOCKUP"}


def answer_for_intent(intent: str, slots: Dict[str, Any],
                      cruise_knots: float) -> Optional[Dict[str, Any]]:
    """Returns None for crossing_safety, which the advisory engine handles."""
    ground = slots.get("ground_id") or DEFAULT_GROUND
    if intent == "nearest_pfz":
        return nearest_pfz(ground)
    if intent == "geofence_check":
        return geofence_check(ground)
    if intent == "route_advisory":
        return route_advisory(slots.get("ground_id") or "G-QUILON", cruise_knots)
    if intent == "productivity":
        return {
            "kind": "productivity",
            "answer": ("Chlorophyll and SST anomalies are on the Researcher view. This "
                       "prototype derives them from the wave record rather than measuring "
                       "them, so they indicate correlation only and cannot predict fish "
                       "availability."),
            "status": "MOCKUP",
        }
    if intent == "greeting":
        return {
            "kind": "greeting",
            "answer": "Hello! I am the ORCA coastal safety advisor. I can help you check crossing conditions, route advisories, and fishing zones. What would you like to know?",
            "status": "MOCKUP",
        }
    return None
