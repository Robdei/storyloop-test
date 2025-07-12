"""Celery task posting to HunyuanVideo cluster."""
from ..cluster import ensure_cluster, mark_prompt

import os, requests
from ..celery_app import celery_app
from ..extensions import db, socketio
from ..models import Scene

ENDPOINT = os.getenv("HUNYUAN_ENDPOINT")

@celery_app.task(name="tasks.generate_scene_hunyuan")
def generate_scene_hunyuan(scene_id: int):
    if ENDPOINT is None:
        return
    with db.session.begin():
        scene: Scene = db.session.get(Scene, scene_id)
        if not scene:
            return
        scene.status = "rendering"
        ensure_cluster()
        mark_prompt()
    try:
        r = requests.post(ENDPOINT, ...)
        r.raise_for_status()
        url = r.json()["video_url"]
        with db.session.begin():
            scene.video_url = url
            scene.status = "done"
        socketio.emit("scene_ready", {"story_id": scene.story_id,"scene_id": scene.id,"video_url": url}, to=scene.story_id)
    except Exception as exc:  # noqa: BLE001
        with db.session.begin():
            scene.status = "error"
        socketio.emit("scene_error", {"story_id": scene.story_id,"scene_id": scene.id,"error": str(exc)}, to=scene.story_id)
        raise