# from celery import Celery
# from app.core.config import settings

# # Initialize Celery
# # "worker" is the name of the main module
# celery_app = Celery(
#     "worker",
#     broker=settings.REDIS_URL,
#     backend=settings.REDIS_URL,
#     broker_connection_retry_on_startup=True,
# )

# # Add robust, professional configurations.
# celery_app.conf.update(
#     task_track_started=True,
#     task_serializer="json",
#     accept_content=["json"],
#     result_serializer="json",
#     timezone="UTC",
#     enable_utc=True,
# )

# celery_app.conf.imports = [
#     "app.tasks.email_tasks",
# ]


from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "worker",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    broker_connection_retry_on_startup=True,
)

celery_app.conf.update(
    # Core
    task_track_started=True,
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    # Reliability
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_reject_on_worker_lost=True,
    # Retries
    task_default_retry_delay=30,
    task_max_retries=5,
    # Timeouts
    task_soft_time_limit=25,
    task_time_limit=30,
)

celery_app.conf.imports = [
    "app.tasks.email_tasks",
]
