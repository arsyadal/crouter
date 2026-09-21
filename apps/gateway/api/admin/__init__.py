from fastapi import APIRouter
from apps.gateway.api.admin.keys import router as keys_router
from apps.gateway.api.admin.routes import router as routes_router
from apps.gateway.api.admin.overview import router as overview_router

admin_router = APIRouter(prefix="/admin")
admin_router.include_router(keys_router)
admin_router.include_router(routes_router)
admin_router.include_router(overview_router)

__all__ = ["admin_router"]
