# GCP Cloud Run Automated Deployment Script for Google Meridian MCP Server
# Domain Target: google-meridian.mcp.borobudur.ai
# GCP Project ID: borobudurai2005

$PROJECT_ID = "borobudurai2005"
$SERVICE_NAME = "google-meridian-mcp"
$REGION = "us-central1"
$CUSTOM_DOMAIN = "google-meridian.mcp.borobudur.ai"

Write-Host "1. Setting GCP Active Project to $PROJECT_ID..." -ForegroundColor Green
gcloud config set project $PROJECT_ID

Write-Host "2. Enabling Cloud Run & Cloud Build APIs..." -ForegroundColor Green
gcloud services enable run.googleapis.com cloudbuild.googleapis.com

Write-Host "3. Submitting Container Build to Cloud Build..." -ForegroundColor Green
gcloud builds submit --tag "gcr.io/$PROJECT_ID/$SERVICE_NAME" .

Write-Host "4. Deploying to Cloud Run..." -ForegroundColor Green
gcloud run deploy $SERVICE_NAME `
  --image "gcr.io/$PROJECT_ID/$SERVICE_NAME" `
  --platform managed `
  --region $REGION `
  --allow-unauthenticated `
  --port 8080

Write-Host "5. Mapping Custom Subdomain: $CUSTOM_DOMAIN..." -ForegroundColor Green
gcloud run domain-mappings create `
  --service $SERVICE_NAME `
  --domain $CUSTOM_DOMAIN `
  --region $REGION

Write-Host "`nSuccessfully deployed! Check gcloud domain mapping output for CNAME/A record DNS configuration." -ForegroundColor Yellow
