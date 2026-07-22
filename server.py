"""
Google Meridian MCP Server (google-meridian-mcp).

Provides tools for AI assistants to discover, search, fetch, and parse
Google Meridian documentation, API reference pages, and GitHub source code.
Features enterprise structured logging, Prometheus metrics, rate limiting,
and pure ASGI SSE transport routing.
"""

import os
import json
import re
import time
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional

import httpx
from bs4 import BeautifulSoup
import markdownify
from mcp.server.fastmcp import FastMCP
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

# Configure Structured Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("google-meridian-mcp")

# Prometheus Metrics
TOOL_CALL_COUNTER = Counter(
    "mcp_tool_calls_total", 
    "Total number of MCP tool calls executed", 
    ["tool_name", "status"]
)
TOOL_LATENCY_HISTOGRAM = Histogram(
    "mcp_tool_execution_time_seconds", 
    "Execution latency of MCP tools in seconds", 
    ["tool_name"]
)

# Server Start Time for Uptime Tracking
SERVER_START_TIME = time.time()

# Simple In-Memory Rate Limiter (100 requests / min per IP)
IP_REQUEST_COUNTS: Dict[str, List[float]] = {}
RATE_LIMIT_MAX_REQUESTS = 100
RATE_LIMIT_WINDOW_SECONDS = 60

# Initialize FastMCP Server
mcp = FastMCP("google-meridian-mcp")

# Local cache directory for fetched & parsed documentation
CACHE_DIR = Path(__file__).parent / ".cache"
CACHE_DIR.mkdir(exist_ok=True)

ALLOWED_DOMAINS = [
    "developers.google.com",
    "github.com",
    "raw.githubusercontent.com"
]

def _log_structured(severity: str, message: str, **kwargs):
    """Outputs structured JSON logs compatible with Google Cloud Logging."""
    log_entry = {
        "severity": severity,
        "message": message,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "service": "google-meridian-mcp",
        **kwargs
    }
    print(json.dumps(log_entry), flush=True)

def _is_url_allowed(url: str) -> bool:
    """Verifies that the requested URL belongs to authorized Google / GitHub domains and prevents SSRF."""
    blocked_patterns = [
        r"169\.254\.169\.254",
        r"10\.\d+\.\d+\.\d+",
        r"192\.168\.\d+\.\d+",
        r"127\.0\.0\.1",
        r"localhost"
    ]
    if any(re.search(pattern, url) for pattern in blocked_patterns):
        return False

    return any(domain in url for domain in ALLOWED_DOMAINS)

def _sanitize_filename(url: str) -> str:
    """Converts a URL into a safe filename for disk caching."""
    clean = re.sub(r'https?://', '', url)
    clean = re.sub(r'[/\\?%*:|"<>]', '_', clean)
    return clean[:150] + ".md"

def _extract_page_links(soup: BeautifulSoup, base_url: str) -> List[str]:
    """Extracts internal documentation and GitHub sub-links from the HTML page."""
    links = set()
    for a_tag in soup.find_all("a", href=True):
        href = a_tag["href"]
        if href.startswith("/meridian"):
            links.add(f"https://developers.google.com{href}")
        elif href.startswith("https://developers.google.com/meridian"):
            links.add(href)
        elif href.startswith("https://github.com/google/meridian"):
            links.add(href)
    return sorted(list(links))[:15]

def _parse_ipynb_cells(notebook_json: Dict[str, Any]) -> str:
    """Parses a Jupyter Notebook JSON object into clean Markdown text."""
    markdown_lines = []
    cells = notebook_json.get("cells", [])
    
    for idx, cell in enumerate(cells, 1):
        cell_type = cell.get("cell_type", "code")
        source = "".join(cell.get("source", []))
        
        if cell_type == "markdown":
            markdown_lines.append(source + "\n")
        elif cell_type == "code":
            markdown_lines.append(f"\n```python\n{source}\n```\n")
            
    return "\n".join(markdown_lines)


@mcp.tool()
def list_doc_sources(category: str = "ALL") -> str:
    """Lists all available Google Meridian documentation sources, guides, and GitHub repositories.
    
    Args:
        category: Filter category ('ALL', 'OVERVIEW_AND_SETUP', 'PRE_MODELING', 
                  'MODELING_AND_FITTING', 'POST_MODELING_AND_OPTIMIZATION', 
                  'ADVANCED_MODELING', 'API_REFERENCE', 'GITHUB_REPOSITORY').
    
    Returns:
        Formatted string listing available documentation sources and URLs.
    """
    from doc_index import MERIDIAN_DOC_SOURCES
    start_time = time.time()
    category_upper = category.upper()
    
    try:
        output = []
        output.append("# Google Meridian Documentation Sources\n")

        if category_upper in MERIDIAN_DOC_SOURCES:
            sources_to_show = {category_upper: MERIDIAN_DOC_SOURCES[category_upper]}
        else:
            sources_to_show = MERIDIAN_DOC_SOURCES

        for cat, items in sources_to_show.items():
            output.append(f"## Category: {cat.replace('_', ' ')}")
            for item in items:
                output.append(f"- **{item['title']}**")
                output.append(f"  - URL: {item['url']}")
                output.append(f"  - Summary: {item['description']}\n")

        output.append("\n*Call `fetch_docs(url)` to get the markdown content of any URL above.*")
        
        duration = time.time() - start_time
        TOOL_CALL_COUNTER.labels(tool_name="list_doc_sources", status="success").inc()
        TOOL_LATENCY_HISTOGRAM.labels(tool_name="list_doc_sources").observe(duration)
        _log_structured("INFO", "Executed list_doc_sources", category=category, duration_ms=round(duration * 1000, 2))
        
        return "\n".join(output)
    except Exception as e:
        TOOL_CALL_COUNTER.labels(tool_name="list_doc_sources", status="error").inc()
        _log_structured("ERROR", f"Error in list_doc_sources: {str(e)}")
        raise e


@mcp.tool()
def fetch_docs(url: str, extract_links: bool = True) -> str:
    """Fetches and parses Google Meridian documentation, API reference pages, or GitHub source code into clean Markdown.
    
    Args:
        url: The URL to fetch documentation from (developers.google.com or github.com).
        extract_links: Whether to list related sub-page URLs found on the page.
    
    Returns:
        Parsed clean Markdown text of the documentation page.
    """
    start_time = time.time()
    
    if not _is_url_allowed(url):
        TOOL_CALL_COUNTER.labels(tool_name="fetch_docs", status="blocked_ssrf").inc()
        _log_structured("WARNING", "Blocked unauthorized or SSRF URL attempt", requested_url=url)
        return f"Error: URL '{url}' is not from an allowed domain. Allowed domains: {ALLOWED_DOMAINS}"

    # Check local disk cache
    cache_file = CACHE_DIR / _sanitize_filename(url)
    if cache_file.exists():
        try:
            content = cache_file.read_text(encoding="utf-8")
            duration = time.time() - start_time
            TOOL_CALL_COUNTER.labels(tool_name="fetch_docs", status="cache_hit").inc()
            TOOL_LATENCY_HISTOGRAM.labels(tool_name="fetch_docs").observe(duration)
            _log_structured("INFO", "Served fetch_docs from cache", url=url, duration_ms=round(duration * 1000, 2))
            return content
        except Exception:
            pass

    # Normalize GitHub URL if pointing to raw file
    fetch_target_url = url
    if "github.com" in url and "/blob/" in url:
        fetch_target_url = url.replace("github.com", "raw.githubusercontent.com").replace("/blob/", "/")

    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) GoogleMeridianMCP/1.0"}
        response = httpx.get(fetch_target_url, headers=headers, follow_redirects=True, timeout=15.0)
        response.raise_for_status()
        content_type = response.headers.get("content-type", "")

        # Case 1: Jupyter Notebook (.ipynb)
        if url.endswith(".ipynb") or "application/json" in content_type:
            try:
                nb_data = response.json()
                md_content = f"# Jupyter Notebook: {url}\n\n" + _parse_ipynb_cells(nb_data)
                cache_file.write_text(md_content, encoding="utf-8")
                
                duration = time.time() - start_time
                TOOL_CALL_COUNTER.labels(tool_name="fetch_docs", status="success").inc()
                TOOL_LATENCY_HISTOGRAM.labels(tool_name="fetch_docs").observe(duration)
                _log_structured("INFO", "Fetched Jupyter Notebook doc", url=url, duration_ms=round(duration * 1000, 2))
                return md_content
            except Exception:
                pass

        # Case 2: Raw Code or Markdown file (.py, .md, raw GitHub)
        if "raw.githubusercontent.com" in fetch_target_url or url.endswith(".py") or url.endswith(".md"):
            raw_text = response.text
            if url.endswith(".py"):
                md_content = f"# Python Source File: {url}\n\n```python\n{raw_text}\n```"
            else:
                md_content = f"# Source: {url}\n\n{raw_text}"
            cache_file.write_text(md_content, encoding="utf-8")
            
            duration = time.time() - start_time
            TOOL_CALL_COUNTER.labels(tool_name="fetch_docs", status="success").inc()
            TOOL_LATENCY_HISTOGRAM.labels(tool_name="fetch_docs").observe(duration)
            _log_structured("INFO", "Fetched raw code/markdown file", url=url, duration_ms=round(duration * 1000, 2))
            return md_content

        # Case 3: HTML Web Page (developers.google.com)
        html = response.text
        soup = BeautifulSoup(html, "html.parser")

        # Extract main article container
        main_article = (
            soup.find("devsite-content") or
            soup.find("article") or
            soup.find("div", class_="devsite-article-body") or
            soup.find("main") or
            soup.body
        )

        if not main_article:
            main_article = soup

        # Strip nav, script, style, header, footer elements
        for element in main_article.find_all(["script", "style", "nav", "devsite-header", "devsite-footer", "devsite-cookie-notification-bar"]):
            element.decompose()

        # Convert to Markdown
        md_text = markdownify.markdownify(str(main_article), heading_style="ATX")
        md_text = re.sub(r'\n{3,}', '\n\n', md_text).strip()

        result = [f"# Source: {url}\n"]
        result.append(md_text)

        if extract_links:
            found_links = _extract_page_links(soup, url)
            if found_links:
                result.append("\n---\n### Sub-Page Documentation Links Found:")
                for link in found_links:
                    result.append(f"- {link}")

        final_markdown = "\n\n".join(result)
        cache_file.write_text(final_markdown, encoding="utf-8")
        
        duration = time.time() - start_time
        TOOL_CALL_COUNTER.labels(tool_name="fetch_docs", status="success").inc()
        TOOL_LATENCY_HISTOGRAM.labels(tool_name="fetch_docs").observe(duration)
        _log_structured("INFO", "Fetched and parsed HTML doc", url=url, duration_ms=round(duration * 1000, 2))
        return final_markdown

    except Exception as e:
        TOOL_CALL_COUNTER.labels(tool_name="fetch_docs", status="error").inc()
        _log_structured("ERROR", f"Error fetching documentation: {str(e)}", url=url)
        return f"Error fetching documentation from '{url}': {str(e)}"


@mcp.tool()
def search_doc_topics(query: str) -> str:
    """Searches Google Meridian documentation by topic or keyword (e.g., 'adstock', 'priors', 'budget optimizer', 'NUTS', 'R-hat').
    
    Args:
        query: Keyword or topic to search for.
    
    Returns:
        Matching documentation links and category locations.
    """
    from doc_index import MERIDIAN_DOC_SOURCES, TOPIC_KEYWORDS
    start_time = time.time()
    query_clean = query.strip().lower()
    matches = []

    for keyword, items in TOPIC_KEYWORDS.items():
        if keyword in query_clean or query_clean in keyword:
            matches.extend(items)

    if not matches:
        # Fallback search across title & description
        for cat, items in MERIDIAN_DOC_SOURCES.items():
            for item in items:
                if (query_clean in item["title"].lower() or 
                    query_clean in item["description"].lower()):
                    matches.append(item)

    duration = time.time() - start_time
    TOOL_CALL_COUNTER.labels(tool_name="search_doc_topics", status="success").inc()
    TOOL_LATENCY_HISTOGRAM.labels(tool_name="search_doc_topics").observe(duration)
    _log_structured("INFO", "Executed search_doc_topics", query=query, duration_ms=round(duration * 1000, 2))

    if not matches:
        return f"No direct documentation match found for topic '{query}'. Try searching for terms like 'data', 'priors', 'budget', 'install', 'MCMC', or 'visualizer'."

    # Deduplicate matches
    unique_matches = {item["url"]: item for item in matches}.values()

    output = [f"# Topic Search Results for '{query}'\n"]
    for item in unique_matches:
        output.append(f"- **{item['title']}**")
        output.append(f"  - URL: {item['url']}")
        output.append(f"  - Summary: {item['description']}\n")

    output.append("*Use `fetch_docs(url)` to view the full content of any page above.*")
    return "\n".join(output)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8080"))
    mode = os.environ.get("MCP_MODE", "stdio").lower()
    
    if mode == "sse" or "PORT" in os.environ:
        _log_structured("INFO", f"Starting Google Meridian MCP Server in SSE Mode on 0.0.0.0:{port}")
        import uvicorn
        from starlette.responses import JSONResponse, Response

        sse_app = mcp.sse_app()

        async def main_app(scope, receive, send):
            if scope["type"] == "http":
                path = scope["path"]
                method = scope["method"]

                # Health Check
                if path == "/health":
                    response = JSONResponse({
                        "status": "HEALTHY",
                        "uptime_seconds": round(time.time() - SERVER_START_TIME, 2),
                        "cache_items": len(list(CACHE_DIR.glob("*.md")))
                    }, status_code=200)
                    await response(scope, receive, send)
                    return

                # Prometheus Metrics
                if path == "/metrics":
                    response = Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
                    await response(scope, receive, send)
                    return

                # Homepage Info
                if path == "/" and method == "GET":
                    response = JSONResponse({
                        "status": "online",
                        "server": "google-meridian-mcp",
                        "mcp_version": "1.0.0",
                        "sse_endpoint": "/sse",
                        "messages_endpoint": "/messages/",
                        "metrics_endpoint": "/metrics",
                        "uptime_seconds": round(time.time() - SERVER_START_TIME, 2),
                        "cache_size_items": len(list(CACHE_DIR.glob("*.md")))
                    })
                    await response(scope, receive, send)
                    return

            # Delegate all MCP requests (GET /sse, POST /messages, initialize, tools, etc.) to FastMCP sse_app!
            await sse_app(scope, receive, send)

        uvicorn.run(main_app, host="0.0.0.0", port=port)
    else:
        mcp.run()
