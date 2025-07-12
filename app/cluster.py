"""Lightweight client that checks Firestore and publishes Pub/Sub messages."""
import os, datetime
from google.cloud import pubsub_v1, firestore

PROJECT = os.environ.get("GCP_PROJECT")
TOPIC_CREATE = os.getenv("PUBSUB_TOPIC_CREATE", "gke-create")
COLL = os.getenv("FIRESTORE_COLLECTION", "cluster-meta")

_pub = pubsub_v1.PublisherClient()
_fs  = firestore.Client()

def ensure_cluster():
    """Publish a create message if cluster missing or deleted."""
    _pub.publish(f"projects/{PROJECT}/topics/{TOPIC_CREATE}", b"start")


def mark_prompt():
    _fs.collection(COLL).document("state").set({"last_prompt": firestore.SERVER_TIMESTAMP})