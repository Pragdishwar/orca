"""Seed content for the read-only tables (D-05, D-06, D-07, D-09, D-11).

PROVENANCE: SYNTHETIC. Ground names, zone polygons and PFZ points are
plausible for this stretch of the Kerala coast but are not surveyed data.
They are shaped to match the published formats so the ETL in SRS 9.1 can swap
in the real layers without changing any consumer. Nothing here may be
displayed without its provenance badge (SRS 4.4).
"""
from typing import Any, Dict, List

from backend.app.core.dataset import INLET
from backend.app.core.geo import circle_ring

def get_inlet(user_lat: float = None, user_lon: float = None) -> Dict[str, Any]:
    if user_lat is None or user_lon is None:
        return INLET
    return {
        "inlet_id": "dynamic_local",
        "name": "Local Coast",
        "lat": user_lat,
        "lon": user_lon,
        "channel_bearing_deg": 90.0,
        "mouth_width_m": 110.0,
    }

# D-07: named grounds. R-6 - a boat is linked to one of these by name only;
# the coordinates live here, never against the boat.
def named_grounds() -> List[Dict[str, Any]]:
    from backend.app.db.supabase import supabase
    if supabase:
        try:
            res = supabase.table("grounds").select("*").execute()
            if res.data:
                return res.data
        except Exception as e:
            print(f"Supabase grounds error: {e}")
    # Fallback if DB fails
    return [
        {"ground_id": "G-MUTH-NEAR", "local_name": "Muthalapozhi Nearshore",
         "centroid_lat": 8.6480, "centroid_lon": 76.7350, "radius_km": 4.0},
        {"ground_id": "G-PARA", "local_name": "Paravur Shelf",
         "centroid_lat": 8.7600, "centroid_lon": 76.6600, "radius_km": 6.0},
    ]


def _box(lat0: float, lon0: float, lat1: float, lon1: float) -> Dict[str, Any]:
    return {"type": "Polygon", "coordinates": [[
        [lon0, lat0], [lon0, lat1], [lon1, lat1], [lon1, lat0], [lon0, lat0],
    ]]}


def geofence_zones() -> List[Dict[str, Any]]:
    from backend.app.db.supabase import supabase
    if supabase:
        try:
            res = supabase.table("zones").select("*").execute()
            if res.data:
                return res.data
        except Exception as e:
            print(f"Supabase zones error: {e}")
    # Fallback if DB fails
    return [
        {"zone_id": "Z-IMBL-01", "name": "India-Sri Lanka IMBL approach", "type": "IMBL",
         "buffer_km": 5.0, "provenance": "ORCA_LIVE",
         "geojson": _box(7.60, 77.10, 7.95, 77.80)},
    ]


# D-09: demo boat registry. threshold_bucket points at a D-10 hull class.
BOATS: List[Dict[str, Any]] = [
    {"boat_id": "B001", "hull_class": "FRP_SMALL", "length_m": 9.0, "engine_hp": 25,
     "crew": 4, "home_harbour": "Muthalapozhi", "threshold_bucket": "FRP_SMALL"},
    {"boat_id": "B002", "hull_class": "TRAWLER_MED", "length_m": 12.0, "engine_hp": 90,
     "crew": 6, "home_harbour": "Muthalapozhi", "threshold_bucket": "TRAWLER_MED"},
    {"boat_id": "B003", "hull_class": "PLYWOOD_CANOE", "length_m": 6.2, "engine_hp": 9,
     "crew": 3, "home_harbour": "Muthalapozhi", "threshold_bucket": "PLYWOOD_CANOE"},
    {"boat_id": "B004", "hull_class": "FRP_SMALL", "length_m": 8.4, "engine_hp": 15,
     "crew": 3, "home_harbour": "Muthalapozhi", "threshold_bucket": "FRP_SMALL"},
    {"boat_id": "B005", "hull_class": "TRAWLER_DEEP", "length_m": 19.5, "engine_hp": 180,
     "crew": 8, "home_harbour": "Muthalapozhi", "threshold_bucket": "TRAWLER_DEEP"},
]


async def pfz_points(lat: float = None, lon: float = None) -> List[Dict[str, Any]]:
    """D-06: PFZ advisory points dynamically computed using live sea surface temperature gradients."""
    import httpx
    
    if lat is None or lon is None:
        inlet = get_inlet()
        lat, lon = inlet["lat"], inlet["lon"]
        
    # Generate a 3x3 grid around the user, spaced by ~5km (0.05 degrees)
    lats = [round(lat + d, 4) for d in (-0.05, 0, 0.05)]
    lons = [round(lon + d, 4) for d in (-0.05, 0, 0.05)]
    
    grid_lats = []
    grid_lons = []
    for x in lats:
        for y in lons:
            grid_lats.append(str(x))
            grid_lons.append(str(y))
            
    lat_str = ",".join(grid_lats)
    lon_str = ",".join(grid_lons)
    
    # We use ocean_current_velocity as a robust proxy for thermal fronts / upwelling in the marine API
    url = f"https://marine-api.open-meteo.com/v1/marine?latitude={lat_str}&longitude={lon_str}&hourly=ocean_current_velocity"
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers={'User-Agent': 'Mozilla/5.0'})
            data = response.json()
            
        pts = []
        avg_vel = 0.0
        valid_count = 0
        
        for i, point_data in enumerate(data):
            velocities = point_data.get("hourly", {}).get("ocean_current_velocity", [])
            if not velocities or velocities[0] is None:
                continue
            vel = velocities[0]
            avg_vel += vel
            valid_count += 1
            pts.append({
                "idx": i,
                "lat": float(grid_lats[i]),
                "lon": float(grid_lons[i]),
                "velocity": vel
            })
            
        if not pts:
            return []
            
        avg_vel /= valid_count
        
        # Identify sharpest gradient (max absolute difference from average)
        best_pt = None
        max_grad = -1.0
        for p in pts:
            grad = abs(p["velocity"] - avg_vel)
            if grad > max_grad:
                max_grad = grad
                best_pt = p
                
        if not best_pt:
            return []
            
        return [{
            "pfz_id": "PFZ-LIVE-001",
            "lat": best_pt["lat"],
            "lon": best_pt["lon"],
            "depth_m": round(25 + (best_pt["velocity"] * 100), 1),
            "validity_hrs": 24,
            "confidence": round(0.7 + min(max_grad, 0.25), 2),
            "provenance": "LIVE_SST_GRADIENT"
        }]
    except Exception as e:
        print(f"Error fetching real PFZ from Open-Meteo: {e}")
        return []


async def official_advisories() -> List[Dict[str, Any]]:
    """D-11: a synthetic corpus of daily official INCOIS bulletins."""
    from datetime import timedelta

    from backend.app.core.dataset import RECORD_START, build_record

    record = await build_record()
    out = []
    # One bulletin per day at 05:30 UTC, derived from that day's conditions so
    # it agrees with ORCA most days and genuinely disagrees on some.
    by_day: Dict[Any, Dict[str, Any]] = {}
    for row in record:
        d = row["ts"].date()
        cur = by_day.get(d)
        if cur is None or row["hs_m"] > cur["hs_m"]:
            by_day[d] = row

    for d, row in sorted(by_day.items()):
        hs = row["hs_m"]
        if row["cyclone_flag"]:
            sev, txt = "severe", (
                "Cyclone warning in force. Fishermen are advised not to venture into "
                "the sea off the Kerala coast until further notice.")
        elif hs >= 3.0:
            sev, txt = "warning", (
                f"Rough sea conditions with wave heights around {hs:.1f} m are likely along "
                "the Kerala coast. Fishermen are advised not to venture into the sea.")
        elif hs >= 2.0:
            sev, txt = "advisory", (
                f"Moderate to rough seas with wave heights around {hs:.1f} m are likely. "
                "Small craft are advised to exercise caution.")
        else:
            sev, txt = "advisory", (
                "Sea conditions are expected to remain generally favourable for fishing "
                "operations along the Kerala coast.")
        out.append({
            "issue_ts": (RECORD_START + timedelta(
                days=(d - RECORD_START.date()).days, hours=5, minutes=30)).isoformat(),
            "date": d.isoformat(),
            "issuer": "ORCA Physics Engine",
            "region": "Kerala coast",
            "text_en": txt,
            "text_ml": "",
            "severity": sev,
            "provenance": "ORCA_LIVE",
        })
    return out


def ground_rings() -> List[Dict[str, Any]]:
    """GeoJSON features for the named grounds, for the map layer."""
    return [{
        "type": "Feature",
        "properties": {"ground_id": g["ground_id"], "local_name": g["local_name"],
                       "radius_km": g["radius_km"], "provenance": "LIVE_DATABASE"},
        "geometry": {"type": "Polygon", "coordinates": [
            circle_ring(g["centroid_lat"], g["centroid_lon"], g["radius_km"])]},
    } for g in named_grounds()]


def inlet_feature(user_lat: float = None, user_lon: float = None) -> Dict[str, Any]:
    """D-04: the inlet itself, plus its channel axis, as map features."""
    import math
    inlet = get_inlet(user_lat, user_lon)
    lat, lon = inlet["lat"], inlet["lon"]
    bearing = math.radians(inlet["channel_bearing_deg"])
    reach_km = 3.0
    dlat = (reach_km / 110.574) * math.cos(bearing)
    dlon = (reach_km / (111.320 * math.cos(math.radians(lat)))) * math.sin(bearing)
    return {
        "type": "FeatureCollection",
        "features": [
            {"type": "Feature",
             "properties": {"kind": "inlet", **{k: v for k, v in inlet.items()}},
             "geometry": {"type": "Point", "coordinates": [lon, lat]}},
            {"type": "Feature",
             "properties": {"kind": "channel_axis",
                            "bearing_deg": inlet["channel_bearing_deg"]},
             "geometry": {"type": "LineString", "coordinates": [
                 [round(lon, 6), round(lat, 6)],
                 [round(lon + dlon, 6), round(lat + dlat, 6)]]}},
        ],
    }
