source ./configs/.project_env

# Enable Private Google Access
gcloud compute networks subnets update default --region $DATA_LOCATION --no-enable-private-ip-google-access