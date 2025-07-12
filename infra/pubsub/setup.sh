set -e
PROJECT=$(gcloud config get-value project)
gcloud pubsub topics create $PUBSUB_TOPIC_CREATE || true
gcloud pubsub topics create $PUBSUB_TOPIC_DELETE || true