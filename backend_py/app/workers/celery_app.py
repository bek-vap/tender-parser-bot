from celery import Celery
from celery.schedules import crontab

from app.core.config import settings

celery_app = Celery(
    "tender_intelligence",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.workers.tasks"],
)

celery_app.conf.timezone = "Asia/Tashkent"
celery_app.conf.task_serializer = "json"
celery_app.conf.result_serializer = "json"
celery_app.conf.accept_content = ["json"]

celery_app.conf.beat_schedule = {
    "scrape-uzex-etender": {
        "task": "app.workers.tasks.scrape_uzex_etender",
        "schedule": crontab(hour=settings.SCRAPE_HOUR, minute=settings.SCRAPE_MINUTE),
    },
    "scrape-xarid-uzex": {
        "task": "app.workers.tasks.scrape_xarid_uzex",
        "schedule": crontab(hour=settings.SCRAPE_HOUR, minute=settings.SCRAPE_MINUTE),
    },
    "scrape-tender-mc": {
        "task": "app.workers.tasks.scrape_tender_mc",
        "schedule": crontab(hour=settings.SCRAPE_HOUR, minute=settings.SCRAPE_MINUTE),
    },
    "scrape-e-auksion": {
        "task": "app.workers.tasks.scrape_e_auksion",
        "schedule": crontab(hour=settings.SCRAPE_HOUR, minute=settings.SCRAPE_MINUTE),
    },
    "process-winners-daily": {
        "task": "app.workers.tasks.process_winners",
        "schedule": crontab(
            hour=settings.WINNER_CHECK_HOUR,
            minute=settings.WINNER_CHECK_MINUTE,
        ),
    },
    "enrich-companies-daily": {
        "task": "app.workers.tasks.enrich_companies",
        "schedule": crontab(hour=10, minute=0),
    }
}
