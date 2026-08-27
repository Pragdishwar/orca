from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from backend.app.api.endpoints import (
    session_router,
    query_router,
    trace_router,
    advisory_router,
    validation_router,
    geospatial_router,
    boats_router,
    registry_router,
    alerts_router,
    demo_router,
    health_router,
    sentinel_router
)

app = FastAPI(
    title="ORCA API",
    description="Backend API for the ORCA project.",
    version="1.0.0"
)

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173", "http://127.0.0.1:3000", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Standardized Error Handlers
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"status": "error", "message": exc.detail},
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={"status": "error", "message": "Validation Error", "details": exc.errors()},
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"status": "error", "message": "Internal Server Error"},
    )

# Include Routers
app.include_router(session_router, prefix="/api/session", tags=["Session"])
app.include_router(query_router, prefix="/api/query", tags=["Query"])
app.include_router(trace_router, prefix="/api/trace", tags=["Trace"])
app.include_router(advisory_router, prefix="/api/advisory", tags=["Advisory"])
app.include_router(validation_router, prefix="/api/validation", tags=["Validation"])
app.include_router(geospatial_router, prefix="/api", tags=["Geospatial"]) # /geofence/check, /pfz/nearest, /route, /productivity inside
app.include_router(boats_router, prefix="/api/boats", tags=["Boats"])
app.include_router(registry_router, prefix="/api", tags=["Registry"]) # /registry, /sources inside
app.include_router(alerts_router, prefix="/api/alerts", tags=["Alerts"])
app.include_router(demo_router, prefix="/api/demo", tags=["Demo"])
app.include_router(health_router, prefix="/api/health", tags=["Health"])
app.include_router(sentinel_router, prefix="/api/sentinel", tags=["Sentinel"])
