#!/usr/bin/env bash
# GCP Cloud Run Automated Deployment Script for Google Meridian MCP Server
# Domain Target: google-meridian.mcp.borobudur.ai
# GCP Project ID: borobudurai2005

set -e

PROJECT_ID="borobudurai2005"
SERVICE_NAME="google-meridian-mcp"
REGION="us-central1"
CUSTOM_DOMAIN="google-meridian.mcp.borobudur.ai"

echo "1. Setting GCP Active Project to $PROJECT_ID..."
gcloud config set project $PROJECT_ID

echo "2. Enabling Cloud Run & Cloud Build APIs..."
gcloud services enable run.googleapis.com cloudbuild.googleapis.com

echo "3. Submitting Container Build to Cloud Build..."
gcloud builds submit --tag "gcr.io/$PROJECT_ID/$SERVICE_NAME" .

echo "4. Deploying to Cloud Run..."
gcloud run deploy $SERVICE_NAME \
  --image "gcr.io/$PROJECT_ID/$SERVICE_NAME" \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --port 8080

echo "5. Mapping Custom Subdomain: $CUSTOM_DOMAIN..."
gcloud run domain-mappings create \
  --service $SERVICE_NAME \
  --domain $CUSTOM_DOMAIN \
  --region $REGION

echo "Successfully deployed! Update your DNS settings for $CUSTOM_DOMAIN as indicated above."
