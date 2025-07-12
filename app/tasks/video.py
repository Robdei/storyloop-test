"""Background task that calls Google Veo 3, uploads MP4 to GCS, updates DB, and notifies clients."""
import base64
import os
from tempfile import NamedTemporaryFile

from google.cloud import aiplatform, storage
from google.cloud.aiplatform import generativemodels as gm

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..celery_app import celery_app
from ..extensions import db, socketio
from ..models import Scene

aiplatform.init(project=os.getenv("GCP_PROJECT"), location="us-central1")
VIDEO_BUCKET = os.getenv("GCS_BUCKET", "storyloop-render")

# Load once per worker process
VIDEO_MODEL = gm.VideoGenerationModel.from_pretrained("google/veo-3.0-generate-preview")
GCS_CLIENT = storage.Client()


@celery_app.task(name="tasks.generate_scene")
def generate_scene(scene_id: int) -> None:  # noqa: D401
    """Generate video for a scene and push update events."""
    # Mark scene as rendering
    with db.session.begin():
        scene: Scene = db.session.get(Scene, scene_id)
        if not scene:
            return
        scene.status = "rendering"

    try:
        response = VIDEO_MODEL.predict(
            prompt=scene.prompt,
            duration_seconds=scene.duration_secs,
            style_preset=scene.style or "cinematic",
            generate_audio=False,
        )

        # Decode first video (base64) → temp file
        raw = base64.b64decode(response.videos[0].bytes_base64)
        with NamedTemporaryFile(delete=False, suffix=".mp4") as tmp:
            tmp.write(raw)
            tmp_path = tmp.name

        # Upload to GCS
        blob_name = f"{scene.story_id}/{scene.id}.mp4"
        bucket = GCS_CLIENT.bucket(VIDEO_BUCKET)
        blob = bucket.blob(blob_name)
        blob.upload_from_filename(tmp_path, content_type="video/mp4")
        public_url = f"https://storage.googleapis.com/{VIDEO_BUCKET}/{blob_name}"

        # Update DB
        with db.session.begin():
            scene.video_url = public_url
            scene.status = "done"

        # Notify clients
        socketio.emit(
            "scene_ready",
            {"story_id": scene.story_id, "scene_id": scene.id, "video_url": public_url},
            to=scene.story_id,
        )
    except Exception as exc:  # noqa: BLE001
        with db.session.begin():
            scene.status = "error"
        socketio.emit(
            "scene_error",
            {"story_id": scene.story_id, "scene_id": scene.id, "error": str(exc)},
            to=scene.story_id,
        )
        raise