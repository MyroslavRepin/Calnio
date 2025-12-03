# worker/email/celery_app.py
from celery import Celery
import os
from dotenv import load_dotenv

load_dotenv()

REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = os.getenv("REDIS_PORT", "6379")
REDIS_DB_BROKER = os.getenv("REDIS_DB_BROKER", "0")
REDIS_DB_BACKEND = os.getenv("REDIS_DB_BACKEND", "1")

BROKER_URL = f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB_BROKER}"
BACKEND_URL = f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB_BACKEND}"

celery_app = Celery(
    "email_worker",
    broker=BROKER_URL,
    backend=BACKEND_URL,
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    broker_connection_retry_on_startup=True,
    broker_connection_max_retries=None,  # infinite retries
    broker_heartbeat=30,
    task_publish_retry=True,
    task_publish_retry_policy={
        "max_retries": 5,
        "interval_start": 0,  # First retry immediately
        "interval_step": 0.5,  # Increase by 0.5s
        "interval_max": 5,  # Cap at 5s
    },
    broker_transport_options={
        "visibility_timeout": 3600,
        "socket_keepalive": True,
        "retry_on_timeout": True,
    },
)

@celery_app.task(name="health.redis_ping")
def redis_ping():
    """Simple health check task to verify Redis connectivity."""
    return "pong"

# Import task modules to register them with Celery

