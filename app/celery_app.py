"""Celery factory initialised from Flask app config."""
import os
from celery import Celery

celery_app = Celery("storyloop")
celery_app.conf.broker_url = os.getenv("REDIS_URL", "redis://redis:6379/0")
celery_app.conf.result_backend = celery_app.conf.broker_url
celery_app.conf.task_default_queue = "storyloop"
celery_app.conf.accept_content = ["json"]
celery_app.conf.task_serializer = "json"