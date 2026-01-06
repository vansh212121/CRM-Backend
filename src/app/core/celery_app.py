from celery import Celery
from app.core.config import settings

# Initialize Celery
# "worker" is the name of the main module
celery_app = Celery(
    "worker",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    broker_connection_retry_on_startup=True,
)

# Add robust, professional configurations.
celery_app.conf.update(
    task_track_started=True,
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)

celery_app.conf.imports = [
    "app.tasks.email_tasks",
]