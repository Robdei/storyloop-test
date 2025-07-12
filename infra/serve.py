from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from pathlib import Path
import uuid, subprocess, os
from google.cloud import storage

app = FastAPI()
BUCKET = os.getenv("GCS_BUCKET", "storyloop-render")
GCS = storage.Client()

class Job(BaseModel):
    prompt: str
    guidance: float = 8.0
    seed: int | None = None

@app.post("/generate")
def generate(job: Job):
    out_path = f"/tmp/{uuid.uuid4()}.mp4"
    cmd = ["python","HunyuanVideo/demo/inference/txt2vid.py","--prompt",job.prompt,"--output",out_path]
    try:
        subprocess.check_output(cmd, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as exc:
        raise HTTPException(status_code=500, detail=exc.output.decode())

    blob_name = f"hunyuan/{Path(out_path).name}"
    blob = GCS.bucket(BUCKET).blob(blob_name)
    blob.upload_from_filename(out_path, content_type="video/mp4")
    url = f"https://storage.googleapis.com/{BUCKET}/{blob_name}"
    return {"video_url": url}