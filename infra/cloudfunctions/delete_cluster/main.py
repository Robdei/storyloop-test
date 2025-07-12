"""Deletes cluster if idle > CLUSTER_IDLE_MINUTES."""
import os, time, base64, json
from datetime import timedelta, datetime, timezone
from google.cloud import container_v1, firestore

PROJECT = os.environ["GCP_PROJECT"]
REGION  = os.getenv("CLUSTER_REGION", "us-central1")
NAME    = os.getenv("CLUSTER_NAME", "storyloop-ai")
COLL    = os.getenv("FIRESTORE_COLLECTION", "cluster-meta")
IDLE    = int(os.getenv("CLUSTER_IDLE_MINUTES", "60"))

fs = firestore.Client()
container = container_v1.ClusterManagerClient()

def pubsub_entry(event, _):
    doc = fs.collection(COLL).document("state").get()
    if not doc.exists:
        return
    ts = doc.to_dict()["last_prompt"].replace(tzinfo=timezone.utc)
    if datetime.now(timezone.utc) - ts < timedelta(minutes=IDLE):
        return  # still active
    try:
        container.delete_cluster(name=f"projects/{PROJECT}/locations/{REGION}/clusters/{NAME}")
    except Exception:
        pass