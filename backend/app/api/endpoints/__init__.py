from .advisory import router as advisory_router
from .alerts import router as alerts_router
from .boats import router as boats_router
from .coverage import router as coverage_router
from .demo import router as demo_router
from .geospatial import router as geospatial_router
from .health import router as health_router
from .map_layers import router as map_router
from .personas import router as personas_router
from .query import router as query_router
from .registry import router as registry_router
from .sentinel import router as sentinel_router
from .session import router as session_router
from .trace import router as trace_router
from .validation import router as validation_router
from .auth import router as auth_router

__all__ = [
    "advisory_router", "alerts_router", "boats_router", "coverage_router",
    "demo_router", "geospatial_router", "health_router", "map_router",
    "personas_router", "query_router", "registry_router", "sentinel_router",
    "session_router", "trace_router", "validation_router", "auth_router",
]
