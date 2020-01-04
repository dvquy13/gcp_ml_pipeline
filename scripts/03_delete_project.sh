source configs/.project_env

echo "Delete project $GCP_PROJECT..."
gcloud projects delete $GCP_PROJECT