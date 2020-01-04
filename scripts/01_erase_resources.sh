echo "Deleting Cloud Storage bucket $GCS_BUCKET..."
gsutil -m rm -r gs://$GCS_BUCKET

echo "Deleting BigQuery dataset $BQ_DATASET..."
bq rm -r -f -d $GCP_PROJECT:$BQ_DATASET

echo "Deleting Firestore collection iris..."
firebase firestore:delete --project=$GCP_PROJECT -r iris -y