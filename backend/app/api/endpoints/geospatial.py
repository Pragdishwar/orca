from fastapi import APIRouter
from backend.app.schemas.geospatial import GeofenceResponse, PFZResponse, RouteRequest, RouteResponse, ProductivityResponse

router = APIRouter()

@router.get("/geofence/check", response_model=GeofenceResponse)
async def check_geofence(ground_id: str):
    return GeofenceResponse(
        ground_id=ground_id,
        in_imbl=False,
        in_mpa=False,
        distance_to_boundary_km=12.5
    )

@router.get("/pfz/nearest", response_model=PFZResponse)
async def get_nearest_pfz(ground_id: str, limit: int = 5):
    return PFZResponse(
        ground_id=ground_id,
        points=[
            {"lat": 12.0, "lon": 79.5, "score": 0.88, "distance_km": 5.2}
        ]
    )

@router.post("/route", response_model=RouteResponse)
async def calculate_route(request: RouteRequest):
    return RouteResponse(
        corridor_h3=["8a2a1072b59ffff", "8a2a1072b59ffff"],
        distance_nm=45.5,
        eta_hours=4.2,
        risk_score=0.3
    )

@router.get("/productivity", response_model=ProductivityResponse)
async def get_productivity(region: str, from_date: str, to_date: str):
    return ProductivityResponse(
        region=region,
        series=[
            {"date": from_date, "chl_anomaly": 0.5, "sst_anomaly": -0.2}
        ]
    )
