from .sentinel import router as sentinel_router
from .session import router as session_router
from .query import router as query_router
from .trace import router as trace_router
from .advisory import router as advisory_router
from .validation import router as validation_router
from .geospatial import router as geospatial_router
from .boats import router as boats_router
from .registry import router as registry_router
from .alerts import router as alerts_router
from .demo import router as demo_router
from .health import router as health_router

__all__ = [
    "sentinel_router",
    "session_router",
    "query_router",
    "trace_router",
    "advisory_router",
    "validation_router",
    "geospatial_router",
    "boats_router",
    "registry_router",
    "alerts_router",
    "demo_router",
    "health_router"
]
