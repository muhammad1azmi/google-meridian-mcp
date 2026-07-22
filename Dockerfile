# Production Dockerfile for Google Meridian MCP Server
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY server.py doc_index.py instructions.md ./

# Default port for GCP Cloud Run
ENV PORT=8080
ENV MCP_MODE=sse

EXPOSE 8080

CMD ["python", "server.py"]
