# app/tasks/video.py – Veo 2 (Gen AI SDK)

import os, time, base64
from tempfile import NamedTemporaryFile
from google import genai
from google.genai import types
from google.cloud import storage

from ..cluster import mark_prompt
from ..celery_app import celery_app
from ..extensions import db, socketio
from ..models import Scene

VEO_MODEL = os.getenv("VEO_MODEL_ID", "veo-2.0-generate-001")
POLL_SEC   = int(os.getenv("VEO_POLL_SEC", "20"))
BUCKET     = os.getenv("GCS_BUCKET", "storyloop-render")

client  = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
gcs     = storage.Client()

@celery_app.task(name="tasks.generate_scene")
def generate_scene(scene_id: int):
    with db.session.begin():
        scene: Scene = db.session.get(Scene, scene_id)
        if not scene:
            return
        scene.status = "rendering"

    mark_prompt() 

    # 1) Submit the job
    op = client.models.generate_videos(
        model=VEO_MODEL,
        prompt=scene.prompt,
        config=types.GenerateVideosConfig(
            person_generation="dont_allow",
            aspect_ratio="16:9",
        ),
    )

    # 2) Poll until done
    while not op.done:
        time.sleep(POLL_SEC)
        op = client.operations.get(op)

    # 3) Save first video
    raw = op.response.generated_videos[0].video.read()
    with NamedTemporaryFile(delete=False, suffix=".mp4") as tmp:
        tmp.write(raw)
        tmp_path = tmp.name

    # 4) Upload to GCS
    blob_name = f"{scene.story_id}/{scene.id}.mp4"
    blob = gcs.bucket(BUCKET).blob(blob_name)
    blob.upload_from_filename(tmp_path, content_type="video/mp4")
    url = f"https://storage.googleapis.com/{BUCKET}/{blob_name}"

    # 5) DB + live event
    with db.session.begin():
        scene.video_url = url
        scene.status = "done"

    socketio.emit("scene_ready",
        {"story_id": scene.story_id, "scene_id": scene.id, "video_url": url},
        to=scene.story_id,
    )