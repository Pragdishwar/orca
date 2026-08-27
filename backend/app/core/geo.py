"""Deterministic geometry: haversine, bearing, point-in-polygon.

Implemented directly rather than via shapely/geopandas so the prototype has no
compiled geospatial dependency and runs on a clean machine. SRS 5.1 classes all
of these as geometric predicates, not learned components.
"""
import math
from typing import Any, Dict, List, Sequence, Tuple

EARTH_RADIUS_KM = 6371.0088


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = p2 - p1
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * EARTH_RADIUS_KM * math.asin(min(1.0, math.sqrt(a)))


def bearing_deg(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dl = math.radians(lon2 - lon1)
    y = math.sin(dl) * math.cos(p2)
    x = math.cos(p1) * math.sin(p2) - math.sin(p1) * math.cos(p2) * math.cos(dl)
    return (math.degrees(math.atan2(y, x)) + 360.0) % 360.0


def point_in_ring(lat: float, lon: float, ring: Sequence[Sequence[float]]) -> bool:
    """Ray casting. `ring` is GeoJSON order: [[lon, lat], ...]."""
    inside = False
    n = len(ring)
    for i in range(n):
        lon_i, lat_i = ring[i][0], ring[i][1]
        lon_j, lat_j = ring[(i - 1) % n][0], ring[(i - 1) % n][1]
        if (lat_i > lat) != (lat_j > lat):
            x = (lon_j - lon_i) * (lat - lat_i) / (lat_j - lat_i) + lon_i
            if lon < x:
                inside = not inside
    return inside


def distance_to_ring_km(lat: float, lon: float, ring: Sequence[Sequence[float]]) -> float:
    """Shortest distance from a point to a polygon boundary, in km."""
    best = float("inf")
    n = len(ring)
    for i in range(n):
        a = ring[i]
        b = ring[(i + 1) % n]
        best = min(best, _point_segment_km(lat, lon, a[1], a[0], b[1], b[0]))
    return best


def _point_segment_km(lat: float, lon: float,
                      lat_a: float, lon_a: float,
                      lat_b: float, lon_b: float) -> float:
    """Distance to a segment, in a local flat projection.

    Adequate at the few-kilometre scale these zones span.
    """
    kx = 111.320 * math.cos(math.radians(lat))
    ky = 110.574
    px, py = lon * kx, lat * ky
    ax, ay = lon_a * kx, lat_a * ky
    bx, by = lon_b * kx, lat_b * ky
    dx, dy = bx - ax, by - ay
    if dx == 0 and dy == 0:
        return math.hypot(px - ax, py - ay)
    t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)))
    return math.hypot(px - (ax + t * dx), py - (ay + t * dy))


def zone_status(lat: float, lon: float, zone_geojson: Dict[str, Any],
                buffer_km: float) -> Tuple[str, float]:
    """Classify a point against one zone: INSIDE / NEAR / CLEAR, plus distance."""
    ring = zone_geojson["coordinates"][0]
    dist = distance_to_ring_km(lat, lon, ring)
    if point_in_ring(lat, lon, ring):
        return "INSIDE", round(dist, 2)
    if dist <= buffer_km:
        return "NEAR", round(dist, 2)
    return "CLEAR", round(dist, 2)


def circle_ring(lat: float, lon: float, radius_km: float, points: int = 36) -> List[List[float]]:
    """GeoJSON ring approximating a circle, for rendering ground radii."""
    ring = []
    for i in range(points + 1):
        theta = 2 * math.pi * i / points
        dlat = (radius_km / 110.574) * math.cos(theta)
        dlon = (radius_km / (111.320 * math.cos(math.radians(lat)))) * math.sin(theta)
        ring.append([round(lon + dlon, 6), round(lat + dlat, 6)])
    return ring
