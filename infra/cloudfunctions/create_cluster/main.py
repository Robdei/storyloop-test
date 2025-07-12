"""2nd-gen Cloud Function triggered by Pub/Sub to create cluster if absent."""
import os, time, base64, json
from google.cloud import container_v1, firestore, build_v1

PROJECT = os.environ["GCP_PROJECT"]
REGION  = os.getenv("CLUSTER_REGION", "us-central1")
NAME    = os.getenv("CLUSTER_NAME", "storyloop-ai")
COLL    = os.getenv("FIRESTORE_COLLECTION", "cluster-meta")

fs = firestore.Client()
container = container_v1.ClusterManagerClient()
cloudbuild = build_v1.CloudBuildClient()

def cluster_exists() -> bool:
    try:
        container.get_cluster(name=f"projects/{PROJECT}/locations/{REGION}/clusters/{NAME}")
        return True
    except Exception:
        return False


def pubsub_entry(event, _):
    _ = base64.b64decode(event["data"]).decode()
    if cluster_exists():
        fs.collection(COLL).document("state").set({"last_prompt": firestore.SERVER_TIMESTAMP})
        return

    # create Autopilot cluster if missing
    container.create_cluster(
        parent=f"projects/{PROJECT}/locations/{REGION}",
        cluster={"name": NAME, "autopilot": {}}
    )

    # deploy helm chart via Cloud Build once control plane is up
    build = {
        "source": {
            "repo_source": {"repo_name": "storyloop", "branch_name": "main"}
        },
        "steps": [{
            "name": "gcr.io/cloud-builders/gke-deploy",
            "args": ["apply","--filename=infra/helm/hunyuan","--cluster", NAME, "--location", REGION]
        }],
    }
    cloudbuild.create_build(project_id=PROJECT, build=build)
    fs.collection(COLL).document("state").set({"last_prompt": firestore.SERVER_TIMESTAMP})