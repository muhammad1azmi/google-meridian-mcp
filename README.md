# Google Meridian MCP Server (`google-meridian-mcp`)

A knowledge and documentation MCP (Model Context Protocol) server for **Google Meridian** (Marketing Mix Modeling), providing AI assistants with structured access to official guides, API references, topic searching, and GitHub source code parsing.

---

## Domain & Cloud Hosting Configuration

- **Target Custom Subdomain**: `google-meridian.mcp.borobudur.ai`
- **Google Cloud Project**: `borobudurai2005`
- **Platform**: Google Cloud Run (Serverless SSE HTTP Transport)

---

## Deployment to Google Cloud Run

To deploy your server publicly under your `borobudur.ai` domain:

### 1. Run Automated Deployment Script
```powershell
.\deploy.ps1
```

Or using Google Cloud CLI (`gcloud`):

```bash
# Set project
gcloud config set project borobudurai2005

# Build & Deploy
gcloud builds submit --tag gcr.io/borobudurai2005/google-meridian-mcp .
gcloud run deploy google-meridian-mcp --image gcr.io/borobudurai2005/google-meridian-mcp --platform managed --region us-central1 --allow-unauthenticated --port 8080

# Map Custom Subdomain
gcloud run domain-mappings create --service google-meridian-mcp --domain google-meridian.mcp.borobudur.ai --region us-central1
```

### 2. Configure DNS for `borobudur.ai`
In your DNS management provider (Cloudflare, GoDaddy, Namecheap):

1. Add a **CNAME** record:
   - **Name / Host**: `google-meridian.mcp` (or `google-meridian.mcp.borobudur.ai`)
   - **Target / Value**: `ghs.googlehosted.com` (or the CNAME provided by `gcloud domain-mappings`)

Google Cloud automatically issues and renews an SSL/TLS certificate for `https://google-meridian.mcp.borobudur.ai`.

---

## Public Remote Registration in IDEs

Once deployed, users anywhere in the world can add your public MCP server to their Cursor, Claude, or Gemini / Antigravity IDE:

```json
{
  "mcpServers": {
    "google-meridian": {
      "url": "https://google-meridian.mcp.borobudur.ai/sse"
    }
  }
}
```

---

## Local Usage (Stdio Mode)

### Run locally
```bash
python server.py
```

### Local `mcp_config.json`
```json
{
  "mcpServers": {
    "google-meridian-mcp": {
      "command": "python",
      "args": [
        "c:/Users/USER/Documents/google-meridian-mcp/server.py"
      ]
    }
  }
}
```
