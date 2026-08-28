import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException

from backend.app.api.endpoints import (
    advisory_router,
    alerts_router,
    boats_router,
    coverage_router,
    demo_router,
    geospatial_router,
    health_router,
    map_router,
    personas_router,
    query_router,
    registry_router,
    sentinel_router,
    session_router,
    trace_router,
    validation_router,
    auth_router,
)
from backend.app.db.bootstrap import bootstrap

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ENABLE_SENTINEL = os.getenv("ENABLE_SENTINEL", "1") != "0"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Bring the database up and start the Sentinel before serving traffic.

    Doing this here rather than in a separate script is what lets the stack
    come up on a clean machine, and with no DATABASE_URL set it falls back to
    a local SQLite file - no database server required.
    """
    await bootstrap()
    if ENABLE_SENTINEL:
        from backend.app.tasks.sentinel import start_sentinel
        start_sentinel()
    yield
    if ENABLE_SENTINEL:
        from backend.app.tasks.sentinel import stop_sentinel
        stop_sentinel()


app = FastAPI(
    title="ORCA API",
    description="Agentic marine advisory platform for the Muthalapozhi inlet. PS26176.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    return JSONResponse(status_code=exc.status_code,
                        content={"status": "error", "message": exc.detail})


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(status_code=422,
                        content={"status": "error", "message": "Validation Error",
                                 "details": exc.errors()})


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    # Log the cause; a bare "Internal Server Error" with nothing behind it is
    # what made the previous deployment impossible to diagnose.
    logger.exception("Unhandled error on %s %s", request.method, request.url.path)
    return JSONResponse(status_code=500,
                        content={"status": "error", "message": "Internal Server Error",
                                 "detail": str(exc)})


@app.get("/")
async def root():
    return {"name": "ORCA API", "docs": "/docs", "health": "/api/health"}


app.include_router(session_router, prefix="/api/session", tags=["Session"])
app.include_router(query_router, prefix="/api/query", tags=["Query"])
app.include_router(trace_router, prefix="/api/trace", tags=["Trace"])
app.include_router(advisory_router, prefix="/api/advisory", tags=["Advisory"])
app.include_router(validation_router, prefix="/api/validation", tags=["Validation"])
app.include_router(coverage_router, prefix="/api/coverage", tags=["Coverage"])
app.include_router(personas_router, prefix="/api/personas", tags=["Personas"])
app.include_router(map_router, prefix="/api/map/layers", tags=["Map"])
app.include_router(geospatial_router, prefix="/api", tags=["Geospatial"])
app.include_router(boats_router, prefix="/api/boats", tags=["Boats"])
app.include_router(registry_router, prefix="/api", tags=["Registry"])
app.include_router(alerts_router, prefix="/api/alerts", tags=["Alerts"])
app.include_router(demo_router, prefix="/api/demo", tags=["Demo"])
app.include_router(health_router, prefix="/api/health", tags=["Health"])
app.include_router(sentinel_router, prefix="/api/sentinel", tags=["Sentinel"])
app.include_router(auth_router, prefix="/api/auth", tags=["Auth"])

_STATIC = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "static")
if os.path.isdir(_STATIC):
    app.mount("/static", StaticFiles(directory=_STATIC), name="static")
