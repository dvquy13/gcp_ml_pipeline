echo 'Initiating project environment variables...'
source configs/.project_env

echo 'Downloading iris data from some Github repo...'
wget https://gist.githubusercontent.com/curran/a08a1080b88344b0c8a7/raw/639388c2cbc2120a14dcf466e85730eb8be498bb/iris.csv

# Moving downloaded data to the correct folder...
mkdir -p data/raw/
mv iris.csv data/raw/

echo 'Creating GCS bucket $GCS_BUCKET...'
gsutil mb -p $GCP_PROJECT -l $DATA_LOCATION -b on gs://$GCS_BUCKET/

echo 'Copying data to GCS...'
gsutil -m cp -r ./data/raw/iris.csv gs://$GCS_BUCKET/data/raw/

echo 'Creating dataset $BQ_DATASET that has default expiration = 30 days (2,592,000 seconds)...'
bq --location=$DATA_LOCATION mk \
--dataset \
--default_table_expiration 2592000 \
$GCP_PROJECT:$BQ_DATASET

echo 'Importing data from GCS to BigQuery...'
bq --location=$DATA_LOCATION load \
--autodetect \
--source_format=CSV \
$BQ_DATASET.$BQ_ORG_TABLE \
gs://$GCS_BUCKET/data/raw/iris.csv
