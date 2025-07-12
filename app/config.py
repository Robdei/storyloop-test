"""Central configuration class."""
from __future__ import annotations

import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


class Config:  # noqa: D101
    SECRET_KEY: str = os.getenv("SECRET_KEY", "change-me-in-prod")
    SQLALCHEMY_DATABASE_URI: str = os.getenv(
        "DATABASE_URL",
        # Use localhost instead of 'db' for local development
        "postgresql+psycopg2://storyloop:storyloop@localhost:5432/storyloop",
    )
    SQLALCHEMY_TRACK_MODIFICATIONS: bool = False

    CELERY_BROKER_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")  # Changed to localhost
    CELERY_RESULT_BACKEND: str = CELERY_BROKER_URL

    WTF_CSRF_TIME_LIMIT: int = 3600

    # Google Cloud / Veo
    GCP_PROJECT: str | None = os.getenv("GCP_PROJECT")
    GOOGLE_APPLICATION_CREDENTIALS: str | None = os.getenv(
        "GOOGLE_APPLICATION_CREDENTIALS"
    )