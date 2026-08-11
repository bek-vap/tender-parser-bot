from fastapi import APIRouter

from .routes.health import router as health_router
from .routes.keywords import router as keywords_router
from .routes.tasks import router as tasks_router
from .routes.google_sheets import router as google_sheets_router
from .routes.excel_export import router as excel_export_router
from .routes.telegram_monitor import router as telegram_monitor_router
from .routes.winners import router as winners_router
from .routes.company_enrichment import router as company_enrichment_router
from .routes.admin import router as admin_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(keywords_router)
api_router.include_router(tasks_router)
api_router.include_router(google_sheets_router)
api_router.include_router(excel_export_router)
api_router.include_router(telegram_monitor_router)
api_router.include_router(winners_router)
api_router.include_router(company_enrichment_router)
api_router.include_router(admin_router)
