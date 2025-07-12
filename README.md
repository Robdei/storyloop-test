# StoryLoop

**StoryLoop** is an AI-powered, collaborative visual-storytelling app.  
Friends take turns writing prompts; each prompt is auto-rendered into a mini-clip (Google Veo 3 *or* open-source **HunyuanVideo** on your own GPUs). Clips are stitched into a short film you can share.

---

## Feature timeline

| Phase | Highlights |
|-------|------------|
| **1** | Flask factory, Poetry, Docker Compose, Postgres, Redis |
| **2** | SQLAlchemy 2 models, password auth (Flask-Login + WTForms) |
| **3** | Real-time story page via Flask-SocketIO |
| **4a** | Celery worker + Veo 3 integration (video → GCS) |
| **4b** | OSS model path: HunyuanVideo on GKE; engine dropdown |
| **4c** | **Auto-spin GKE cluster** → spins up on first prompt; auto-deletes after 60 min idle |

---

## Quick start (local)

```bash
poetry install --sync
flask db upgrade
python run.py          # http://localhost:5000
```

## Docker stack

```bash
docker compose build
docker compose up -d   # web + worker + db + redis
```

## GPU Auto-Spin 🚀  (Phase 4c)

Slash your GPU bill to $0 while no one is prompting.

What happens
	1.	User prompt → ensure_cluster() publishes a message to Pub/Sub topic gke-create and timestamps Firestore (cluster-meta/state.last_prompt).
	2.	Cloud Function create-cluster sees no cluster ⇒
	•	creates an Autopilot GKE cluster (storyloop-ai) in $CLUSTER_REGION;
	•	installs infra/helm/hunyuan via gke-deploy.
	3.	Celery task calls the Hunyuan FastAPI /generate endpoint; when the clip is ready it uploads to GCS and marks the scene done.
	4.	Every new prompt updates last_prompt; a Cloud Scheduler job publishes to gke-delete every 15 min.
	5.	Function delete-cluster deletes the cluster if now - last_prompt > $CLUSTER_IDLE_MINUTES (default 60 min).
	6.	GPU node-pool (min 0) = $0 while idle; next prompt restarts the cycle.

## One-time setup

```bash
# 1) Build & push model image
REGION=us-central1
PROJECT=$(gcloud config get-value project)
IMAGE="$REGION-docker.pkg.dev/$PROJECT/storyloop/hunyuan:latest"
docker build -f Dockerfile.hunyuan -t "$IMAGE" .
docker push "$IMAGE"

# 2) Create Autopilot cluster + GPU node-pool that can scale to zero
gcloud container clusters create-auto storyloop-ai \
  --region $REGION --release-channel stable
gcloud container node-pools create hunyuan-gpu \
  --cluster storyloop-ai --region $REGION \
  --accelerator type=nvidia-l4,count=1 --machine-type n2-standard-4 \
  --enable-autoscaling --min-nodes 0 --max-nodes 1

# 3) Helm-deploy the model once (CI does this automatically later)
helm upgrade -i hunyuan infra/helm/hunyuan \
  --set image=$IMAGE \
  --kube-context=gke_${PROJECT}_${REGION}_storyloop-ai

# 4) Provision Pub/Sub topics
./infra/pubsub/setup.sh

# 5) Deploy Cloud Functions (gen 2)
gcloud functions deploy create-cluster \
  --gen2 --runtime=python312 --region=$REGION \
  --source=infra/cloudfunctions/create_cluster \
  --trigger-topic=gke-create
gcloud functions deploy delete-cluster \
  --gen2 --runtime=python312 --region=$REGION \
  --source=infra/cloudfunctions/delete_cluster \
  --trigger-topic=gke-delete

# 6) Cloud Scheduler to prune idle clusters
gcloud scheduler jobs create pubsub idle-prune \
  --schedule "*/15 * * * *" --time-zone=UTC \
  --topic gke-delete --message-body "{}"
```

## .env keys

VIDEO_ENGINE=veo                       # veo | hunyuan
HUNYUAN_ENDPOINT=http://hunyuan-service.default.svc.cluster.local:8080/generate
CLUSTER_REGION=us-central1
CLUSTER_NAME=storyloop-ai
CLUSTER_IDLE_MINUTES=60
PUBSUB_TOPIC_CREATE=gke-create
PUBSUB_TOPIC_DELETE=gke-delete
FIRESTORE_COLLECTION=cluster-meta

## Tests and Lint

```bash
poetry run pytest
poetry run black --check app infra
```