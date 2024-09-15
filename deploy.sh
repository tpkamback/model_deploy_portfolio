#!/bin/bash

if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
else
    echo ".env file not found!"
    exit 1
fi

echo "Setting GCP project to $PROJECT_ID"
echo "Setting Cloud Functions region to $REGION"
echo "Setting Bucket name to $BUCKET_NAME"

gcloud config set project "$PROJECT_ID"

echo "Deploying Cloud Function 'update_model'"
gcloud functions deploy update_model \
    --runtime python310 \
    --trigger-http \
    --allow-unauthenticated \
    --entry-point update_model \
    --source deploy/ \
    --region "$REGION" \
    --quiet \
    --set-env-vars BUCKET_NAME=$BUCKET_NAME

# Cloud Schedulerの設定
# echo "Creating Cloud Scheduler job 'daily-model-update'"
# gcloud scheduler jobs create http daily-model-update \
#     --schedule "0 9 * * *" \
#     --uri "https://${REGION}-${PROJECT_ID}.cloudfunctions.net/update_model" \
#     --http-method GET \
#     --time-zone "Asia/Tokyo"

echo "Deployment completed successfully."