source configs/.project_env

echo "Disabling resources..."
gcloud services disable dataproc.googleapis.com
gcloud services disable firestore.googleapis.com