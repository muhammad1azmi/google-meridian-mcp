"""
Google Meridian MCP Server (google-meridian-mcp).

A Cloud-Agnostic, First-Principles Model Context Protocol (MCP) server for Google Meridian
and Marketing Mix Modeling (MMM). Guides data scientists across all 7 control points,
5 workflow phases, 3 iteration loops, probability calculations, model auditing, and code synthesis.

Supports FastMCP stdio, SSE, and direct HTTP POST JSON-RPC transport.
"""

import os
import json
import re
import time
import math
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
    """Outputs structured JSON logs compatible with Cloud Logging."""
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

# -----------------------------------------------------------------------------
# MCP TOOLS: KNOWLEDGE & DOCUMENTATION RETRIEVAL
# -----------------------------------------------------------------------------

@mcp.tool()
def list_doc_sources(category: str = "ALL") -> str:
    """Lists all available Google Meridian documentation sources, guides, and GitHub repositories.
    
    Args:
        category: Filter category ('ALL', 'OVERVIEW_AND_SETUP', 'PRE_MODELING', 
                  'MODELING_AND_FITTING', 'POST_MODELING_AND_OPTIMIZATION', 
                  'ADVANCED_MODELING', 'API_REFERENCE', 'GITHUB_REPOSITORY').
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
    """Fetches and parses Google Meridian documentation, API reference pages, or GitHub source code into clean Markdown."""
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

        main_article = (
            soup.find("devsite-content") or
            soup.find("article") or
            soup.find("div", class_="devsite-article-body") or
            soup.find("main") or
            soup.body
        )

        if not main_article:
            main_article = soup

        for element in main_article.find_all(["script", "style", "nav", "devsite-header", "devsite-footer", "devsite-cookie-notification-bar"]):
            element.decompose()

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
    """Searches Google Meridian documentation by topic or keyword."""
    from doc_index import MERIDIAN_DOC_SOURCES, TOPIC_KEYWORDS
    start_time = time.time()
    query_clean = query.strip().lower()
    matches = []

    for keyword, items in TOPIC_KEYWORDS.items():
        if keyword in query_clean or query_clean in keyword:
            matches.extend(items)

    if not matches:
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

    unique_matches = {item["url"]: item for item in matches}.values()

    output = [f"# Topic Search Results for '{query}'\n"]
    for item in unique_matches:
        output.append(f"- **{item['title']}**")
        output.append(f"  - URL: {item['url']}")
        output.append(f"  - Summary: {item['description']}\n")

    output.append("*Use `fetch_docs(url)` to view the full content of any page above.*")
    return "\n".join(output)


# -----------------------------------------------------------------------------
# MCP TOOLS: DATA SCIENCE CONTROL POINTS & WORKFLOW GUIDANCE
# -----------------------------------------------------------------------------

@mcp.tool()
def get_control_point_guide(control_point: str = "ALL") -> str:
    """Provides operational parameters, mathematical formulas, recommended bounds, and Google Meridian defaults for data science control points.
    
    Args:
        control_point: 'data_inputs', 'confounders_and_dag', 'adstock_decay', 'hill_saturation', 'bayesian_priors', 'mcmc_diagnostics', 'optimization_bounds', or 'ALL'.
    """
    guides = {
        "data_inputs": r"""### Control Point 1: Data Inputs & Metric Selection
- **Granularity**: Weekly (recommended to balance sample size and observational noise).
- **Media Metric Choice**: Use Impressions / Reach & Frequency data over Spend where available to separate volume from CPM inflation.
- **Taxonomy**: Group correlated tactics (e.g., aggregate Google Search + Bing Search if collinearity > 0.8).""",

        "confounders_and_dag": r"""### Control Point 2: Confounders, Seasonality & Baseline
- **Confounders**: Include Price, Promotions, Inflation, and Organic Google Trends to block backdoor causal paths.
- **Seasonality Spline Knots**: 1 knot per 4 to 8 weeks. Avoid knot distance < 3 weeks (causes baseline over-smoothing and media credit theft).""",

        "adstock_decay": r"""### Control Point 3: Adstock Carryover Transformation
- **Geometric Adstock**: $x_{t}^{ad} = \sum_{l=0}^{L} \alpha^{l} x_{t-l}$ where $0 < \alpha < 1$.
- **Weibull Adstock**: LIDF / CDF options for peak-decay kinetics.
- **Max Lag**: Set to 4–12 weeks based on vertical sales cycle length.""",

        "hill_saturation": r"""### Control Point 4: Hill Saturation Curves
- **Hill Equation**: $S(x) = \frac{x^c}{K^c + x^c}$
- **Half-Saturation ($K$)**: Spend level reaching 50% max response.
- **Slope ($c$)**: Curve steepness ($c > 0$).
- **Transformation Order**: `hill_before_adstock=False` is standard in Meridian.""",

        "bayesian_priors": r"""### Control Point 5: Bayesian Prior Calibration & Custom Combinations
- **Prior Specs**: LogNormal$(\mu, \sigma)$, Beta$(\alpha, \beta)$, or Truncated Normal distributions.
- **Lift Test Calibration**: Convert 95% CIs from Geo/Conversion Lift experiments into exact LogNormal parameters.
- **Non-Revenue Priors**: Apply Total Paid Media Contribution Priors when KPI is non-monetary (e.g. leads, app installs).
- **Variance Control**: Avoid overly broad prior variances ($\sigma > 1.5$) on noisy channel data.""",

        "mcmc_diagnostics": r"""### Control Point 6: MCMC Sampling, JAX Backend & Diagnostics
- **Execution Backend**: Standard TensorFlow Probability vs. **JAX Backend** for high-performance GPU/TPU acceleration.
- **Sampler Parameters**: `n_chains=4`, `n_adapt=500–1000`, `n_burnin=500`, `target_accept=0.85–0.95`.
- **Diagnostics & Health Score**: Enforce Gelman-Rubin $\hat{R} < 1.05$, Effective Sample Size $ESS > 400$, zero divergent transitions, and check Meridian `health_score`.""",

        "optimization_bounds": r"""### Control Point 7: Post-Modeling & Optimization Constraints
- **Objective**: Maximize Total Revenue or Target ROAS / mROAS.
- **Feasible Spend Bounds**: Set min/max channel spend multipliers (e.g. $0.8\times$ to $1.2\times$) to avoid out-of-bounds extrapolation.
- **CPMU & Refresh**: Account for future CPM rate increases and set incremental dataset model refresh schedules.""",

        "visualizer_templates": r"""### Control Point 8: Output Visualizer & Pre-Made Chart Templates
- **plot_model_fit**: Actual vs. Predicted time series (filter by `geos`, toggle 95% Credible Intervals).
- **plot_contribution**: Baseline vs. Paid Media decomposition stacked bar / pie charts.
- **plot_response_curves**: Spend vs Incremental outcome saturation curves (toggle ROI vs mROI vs CPIK, spend multiplier $0.0\times - 3.0\times$).
- **plot_adstock_decay**: Time-decay carryover memory curves ($\alpha$).
- **plot_channel_summary**: Channel performance ranking by ROI / mROI / Spend.
- **plot_reach_frequency**: Optimal frequency curves to identify wearout thresholds.
- **plot_optimization_results**: Before vs. After reallocation pie charts & spend deltas ($\Delta \text{Spend}$)."""
    }

    cp_clean = control_point.lower().strip()
    if cp_clean in guides:
        return f"# Meridian Control Point Guide: {cp_clean.upper()}\n\n" + guides[cp_clean]

    if cp_clean == "all":
        output = ["# Google Meridian Comprehensive Control Points Guide\n"]
        for key, text in guides.items():
            output.append(text + "\n")
        return "\n".join(output)

    # Dynamic search fallback for specific control point concepts/keywords
    from doc_index import MERIDIAN_DOC_SOURCES, TOPIC_KEYWORDS
    matches = []
    for keyword, items in TOPIC_KEYWORDS.items():
        if keyword in cp_clean or cp_clean in keyword:
            matches.extend(items)

    if not matches:
        for cat, items in MERIDIAN_DOC_SOURCES.items():
            for item in items:
                if (cp_clean in item["title"].lower() or cp_clean in item["description"].lower()):
                    matches.append(item)

    if matches:
        unique_matches = {item["url"]: item for item in matches}.values()
        output = [f"# Meridian Control Point Guide for '{control_point}'\n"]
        for item in unique_matches:
            output.append(f"- **{item['title']}**")
            output.append(f"  - URL: {item['url']}")
            output.append(f"  - Summary: {item['description']}\n")
        output.append("*Use `fetch_docs(url)` to retrieve complete API reference or guide content.*")
        return "\n".join(output)

    output = [f"# Google Meridian Control Point Guide for '{control_point}'\n"]
    output.append(f"Specific concept '{control_point}' searched across master catalog.\n")
    for key, text in guides.items():
        output.append(text + "\n")
    return "\n".join(output)



@mcp.tool()
def get_mmm_workflow_guide(phase: str = "ALL") -> str:
    """Provides step-by-step decision trees and iteration rules for the 5 modeling phases and 3 iteration loops.
    
    Args:
        phase: 'phase1_data_prep', 'phase2_specification', 'loop_a_convergence', 'loop_b_plausibility', 'loop_c_calibration', 'phase4_optimization', or 'ALL'.
    """
    phases = {
        "phase1_data_prep": "### Phase 1: Data Alignment & Confounder Definition\n- Aggregate data to weekly grain.\n- Specify media metrics (Spend vs Impressions).\n- Identify external confounders (price, promos, seasonality).",
        "phase2_specification": "### Phase 2: Base Specification & Prior Setup\n- Choose adstock decay function & Hill curve order.\n- Set baseline spline knot distance.\n- Set initial Bayesian priors from historical experiments.",
        "loop_a_convergence": "### Loop A: Technical Convergence Check\n- Check Gelman-Rubin $\\hat{R} < 1.05$ and $ESS > 400$.\n- If sampling fails: Increase `n_adapt`, raise `target_accept` to 0.95, or tighten prior variances.",
        "loop_b_plausibility": "### Loop B: Causal Plausibility Check\n- Check Baseline vs Paid Media contribution ratio.\n- If baseline claims >90% sales: Increase knot distance (stiffen baseline).\n- If a channel ROI is unrealistically high (e.g. 50x): Add missing promotional confounders.",
        "loop_c_calibration": "### Loop C: Lift Test Alignment\n- Compare model posterior ROIs against independent Geo Lift tests.\n- Re-anchor LogNormal prior $(\\mu, \\sigma)$ to match 95% confidence intervals from lift tests.",
        "phase4_optimization": "### Phase 4: Budget Optimization & Scenarios\n- Define optimization objective (Max Revenue vs Target ROAS).\n- Apply spend bounds ($0.8\\times - 1.2\\times$).\n- Simulate future scenarios with CPM adjustment multipliers."
    }

    p_clean = phase.lower().strip()
    if p_clean in phases:
        return f"# Meridian Workflow Guide: {p_clean.upper()}\n\n" + phases[p_clean]

    output = ["# Google Meridian Data Science Workflow & Iteration Loops\n"]
    for key, text in phases.items():
        output.append(text + "\n")
    return "\n".join(output)


# -----------------------------------------------------------------------------
# MCP TOOLS: MATH ENGINE, AUDITOR & CODE SYNTHESIZER
# -----------------------------------------------------------------------------

@mcp.tool()
def calculate_bayesian_prior(experiment_type: str = "geo_lift", point_estimate: float = 2.0, ci_lower: float = 1.2, ci_upper: float = 2.8) -> str:
    """Solves exact probability equations to convert 95% Confidence Intervals from Lift Tests into Meridian LogNormal (mu, sigma) prior parameters.
    
    Args:
        experiment_type: Type of experiment ('geo_lift', 'conversion_lift', 'holdout').
        point_estimate: Point estimate ROI or Lift multiplier (e.g. 2.0).
        ci_lower: Lower bound of 95% Confidence Interval (e.g. 1.2).
        ci_upper: Upper bound of 95% Confidence Interval (e.g. 2.8).
    """
    if point_estimate <= 0 or ci_lower <= 0 or ci_upper <= 0:
        return "Error: Prior point estimate and confidence interval bounds must be greater than zero."
    
    if not (ci_lower <= point_estimate <= ci_upper):
        return f"Error: Point estimate ({point_estimate}) must lie between lower bound ({ci_lower}) and upper bound ({ci_upper})."

    # Math Derivation for LogNormal(mu, sigma):
    # mu = ln(point_estimate)
    # sigma = (ln(ci_upper) - ln(ci_lower)) / (2 * 1.96)
    mu = math.log(point_estimate)
    sigma = (math.log(ci_upper) - math.log(ci_lower)) / 3.92

    output = [
        f"# Calculated Meridian LogNormal Prior Parameters",
        f"- **Experiment Type**: {experiment_type}",
        f"- **Point Estimate**: {point_estimate}",
        f"- **95% Confidence Interval**: [{ci_lower}, {ci_upper}]\n",
        f"### Mathematical Derivation:",
        f"- $\\mu = \\ln(\\text{{point\\_estimate}}) = \\ln({point_estimate}) = \\mathbf{{{round(mu, 4)}}}$",
        f"- $\\sigma = \\frac{{\\ln({ci_upper}) - \\ln({ci_lower})}}{{3.92}} = \\mathbf{{{round(sigma, 4)}}}$\n",
        f"### Google Meridian Python Prior Spec Code:",
        f"```python",
        f"import tfp_distributions as tfd # tensorflow_probability",
        f"# Apply to media channel prior spec",
        f"prior_spec = tfd.LogNormal(loc={round(mu, 4)}, scale={round(sigma, 4)})",
        f"```"
    ]
    return "\n".join(output)


@mcp.tool()
def audit_model_first_principles(config_json: str = "{}") -> str:
    """Audits a proposed Google Meridian model specification for identifiability, knot density, prior variance, and Hill parameter bounds."""
    try:
        cfg = json.loads(config_json) if isinstance(config_json, str) and config_json.strip() else {}
    except Exception:
        cfg = {}

    knot_distance = cfg.get("knot_distance_weeks", 6)
    prior_sd = cfg.get("prior_sd", 0.5)
    max_lag = cfg.get("max_lag_weeks", 8)
    n_channels = cfg.get("n_channels", 4)

    warnings = []
    recommendations = []

    if knot_distance < 4:
        warnings.append(f"CRITICAL: Knot distance ({knot_distance} weeks) is too small. Overly flexible baseline will absorb media contributions.")
        recommendations.append("Increase knot_distance_weeks to between 4 and 8 weeks.")
    else:
        recommendations.append(f"Knot distance ({knot_distance} weeks) is within healthy range (4–8 weeks).")

    if prior_sd > 1.2:
        warnings.append(f"WARNING: Prior standard deviation ({prior_sd}) is too uninformative for observational data.")
        recommendations.append("Tighten prior_sd to between 0.3 and 0.8 to prevent degenerate posterior fits.")

    if max_lag > 12:
        warnings.append(f"WARNING: Max lag ({max_lag} weeks) is unusually long for standard adstock carryover.")
        recommendations.append("Set max_lag_weeks to 4–8 weeks unless analyzing high-consideration long-funnel verticals.")

    output = [
        f"# Google Meridian First-Principles Model Spec Audit\n",
        f"### Evaluated Specifications:",
        f"- Knot Distance: {knot_distance} weeks",
        f"- Prior Standard Deviation: {prior_sd}",
        f"- Max Adstock Lag: {max_lag} weeks",
        f"- Channels Analyzed: {n_channels}\n",
        f"### Audit Warnings ({len(warnings)}):"
    ]
    if warnings:
        for w in warnings:
            output.append(f"- ⚠️ {w}")
    else:
        output.append("- ✅ No critical specification risks detected.")

    output.append("\n### Recommendations:")
    for r in recommendations:
        output.append(f"- 💡 {r}")

    return "\n".join(output)


@mcp.tool()
def run_eda_checks(config_json: str = "{}") -> str:
    """Provides guidelines and configuration for Google Meridian Pre-Modeling EDA checks (VIF, Pairwise Correlation, KPI Variance, Data-Parameter Ratio)."""
    return r"""# Google Meridian Pre-Modeling EDA Engine (`meridian.model.eda`)

### 1. Data-to-Parameter Ratio Check (`DataParameterRatioArtifact`)
- Enforces observations ($T \times G$) $\ge 5 \times$ total parameters.
- Prevents under-identified model estimation.

### 2. Variance Inflation Factor Audit (`VIFSpec`)
- Computes $\text{VIF}_m = \frac{1}{1 - R_m^2}$ for media channels and non-media treatments.
- Threshold: Flags channels with $\text{VIF} > 5.0$ for tactic aggregation.

### 3. Pairwise Correlation Matrix (`PairwiseCorrSpec`)
- Evaluates pairwise correlation coefficients ($r$) between spend vectors.
- Flag threshold: $r > 0.85$.

### 4. KPI Invariability Audit (`KpiInvariabilitySpec`)
- Checks target KPI variance across time and geographies.
- Flags flat/uninformative target data."""


@mcp.tool()
def run_model_review_checks(check_type: str = "ALL") -> str:
    """Provides diagnostic checks from Google Meridian Automated Model Review Engine (meridian.analysis.review.checks).
    
    Args:
        check_type: 'baseline', 'bayesian_ppp', 'convergence', 'goodness_of_fit', 'high_variance', 'implausible_roi', 'potential_bias', 'prior_posterior_shift', 'roi_consistency', or 'ALL'.
    """
    checks = {
        "baseline": "### BaselineCheck: Verifies baseline contribution share is realistic (70–80%).",
        "bayesian_ppp": "### BayesianPPPCheck: Computes Posterior Predictive P-value to test model fit distribution.",
        "convergence": "### ConvergenceCheck: Audits Gelman-Rubin $\\hat{R} < 1.05$ and $ESS > 400$.",
        "goodness_of_fit": "### GoodnessOfFitCheck: Measures holdout out-of-sample MAPE, RMSE, and $R^2$.",
        "high_variance": "### HighVarianceCheck: Identifies high posterior variance in channel parameters.",
        "implausible_roi": "### ImplausibleROICheck: Flags negative or non-physically viable ROIs (e.g. 50x+).",
        "potential_bias": "### PotentialBiasCheck: Audits residual patterns for systematic time or geo bias.",
        "prior_posterior_shift": "### PriorPosteriorShiftCheck: Measures KL-divergence shift between prior and posterior distributions.",
        "roi_consistency": "### ROIConsistencyCheck: Verifies ROI stability across rolling sub-windows."
    }

    c_clean = check_type.lower().strip()
    if c_clean in checks:
        return f"# Meridian Review Check: {c_clean.upper()}\n\n" + checks[c_clean]

    output = ["# Google Meridian Model Review Checks (`meridian.analysis.review.checks`)\n"]
    for text in checks.values():
        output.append(text + "\n")
    return "\n".join(output)



@mcp.tool()
def synthesize_meridian_code(pipeline_stage: str = "FULL_PIPELINE", config_json: str = "{}") -> str:
    """Synthesizes clean, portable, cloud-agnostic Python code implementing Google Meridian pipelines."""
    stage_upper = pipeline_stage.upper().strip()

    code_templates = {
        "INPUT_DATA": '''import pandas as pd
from meridian.data import input_data

# 1. Load Cloud-Agnostic Local/Remote Dataset
df = pd.read_csv("meridian_input_data.csv")

# 2. Build Meridian InputData Object
data = input_data.InputData(
    kpi=df["kpi"].values,
    kpi_type="REVENUE",
    media_spend=df[["spend_ch1", "spend_ch2"]].values,
    media_impressions=df[["imp_ch1", "imp_ch2"]].values,
    controls=df[["price_index", "promo_flag"]].values,
    media_channel_names=["Channel_1", "Channel_2"],
    control_variable_names=["Price_Index", "Promo_Flag"]
)''',

        "MODEL_SPEC": '''from meridian.model import spec

# Configure First-Principles Model Specification
model_spec = spec.ModelSpec(
    media_effects_dist="log_normal",
    hill_before_adstock=False,
    knots=13,  # ~1 knot per 8 weeks over 2 years
    max_lag=8
)''',

        "FULL_PIPELINE": '''import pandas as pd
from meridian.data import input_data
from meridian.model import spec, model
from meridian.analysis import optimizer

# 1. Load Data
df = pd.read_csv("meridian_input_data.csv")
data = input_data.InputData(
    kpi=df["kpi"].values,
    kpi_type="REVENUE",
    media_spend=df[["spend_ch1", "spend_ch2"]].values,
    media_impressions=df[["imp_ch1", "imp_ch2"]].values,
    controls=df[["price_index", "promo_flag"]].values,
    media_channel_names=["Channel_1", "Channel_2"],
    control_variable_names=["Price_Index", "Promo_Flag"]
)

# 2. Specify Model
model_spec = spec.ModelSpec(
    media_effects_dist="log_normal",
    hill_before_adstock=False,
    max_lag=8
)

# 3. Fit Model via NUTS MCMC
mmm = model.Meridian(input_data=data, model_spec=model_spec)
mmm.fit(n_chains=4, n_adapt=500, n_burnin=500, n_keep=1000)

# 4. Optimize Budget Allocation
opt = optimizer.BudgetOptimizer(mmm)
opt_results = opt.optimize(min_multiplier=0.8, max_multiplier=1.2)
print(opt_results)'''
    }

    selected_code = code_templates.get(stage_upper, code_templates["FULL_PIPELINE"])
    return f"# Cloud-Agnostic Google Meridian Python Snippet ({stage_upper})\n\n```python\n{selected_code}\n```"


@mcp.tool()
def generate_schema_template(n_weeks: int = 104, n_geos: int = 1, n_channels: int = 3) -> str:
    """Generates a synthetic benchmarking CSV schema template matching Google Meridian's input format."""
    header = ["time", "geo", "kpi"]
    for i in range(1, n_channels + 1):
        header.extend([f"spend_channel_{i}", f"impressions_channel_{i}"])
    header.extend(["control_price_index", "control_promotions"])

    rows = [",".join(header)]
    
    # Generate 3 sample rows
    for week in range(1, 4):
        date_str = f"2025-01-0{week}"
        row_vals = [date_str, "national", str(100000 + week * 2500)]
        for i in range(1, n_channels + 1):
            row_vals.extend([str(15000 + i * 2000), str(500000 + i * 50000)])
        row_vals.extend(["1.02", "1" if week == 2 else "0"])
        rows.append(",".join(row_vals))

    csv_text = "\n".join(rows)

    return f"# Google Meridian Input Schema Template ({n_weeks} weeks, {n_geos} geos, {n_channels} channels)\n\n```csv\n{csv_text}\n```\n\n*Save this format as `meridian_input_data.csv` for cloud-agnostic execution.*"


# -----------------------------------------------------------------------------
# JSON-RPC DISPATCHER FOR DIRECT HTTP POST CLIENTS
# -----------------------------------------------------------------------------

def _handle_jsonrpc_request(body: Dict[str, Any]) -> Dict[str, Any]:
    """Handles direct HTTP POST JSON-RPC MCP requests (initialize, tools/list, tools/call)."""
    req_id = body.get("id")
    method = body.get("method")
    params = body.get("params", {})

    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "google-meridian-mcp", "version": "1.0.0"}
            }
        }

    if method == "notifications/initialized":
        return {"jsonrpc": "2.0", "id": req_id, "result": {}}

    if method == "tools/list":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "tools": [
                    {"name": "list_doc_sources", "description": "Lists all available Google Meridian documentation sources."},
                    {"name": "fetch_docs", "description": "Fetches and parses Google Meridian documentation or code into clean Markdown."},
                    {"name": "search_doc_topics", "description": "Searches Google Meridian documentation by topic or keyword."},
                    {"name": "get_control_point_guide", "description": "Provides operational parameters, math formulas, and bounds for data science control points."},
                    {"name": "get_mmm_workflow_guide", "description": "Provides decision trees and iteration rules for modeling phases and iteration loops."},
                    {"name": "calculate_bayesian_prior", "description": "Solves probability equations to convert 95% CIs into Meridian LogNormal (mu, sigma) prior parameters."},
                    {"name": "audit_model_first_principles", "description": "Audits model spec for identifiability, knot density, prior variance, and Hill parameter bounds."},
                    {"name": "synthesize_meridian_code", "description": "Synthesizes clean, portable, cloud-agnostic Python code for Google Meridian."},
                    {"name": "generate_schema_template", "description": "Generates a synthetic benchmarking CSV schema template matching Meridian's input format."}
                ]
            }
        }

    if method == "tools/call":
        tool_name = params.get("name")
        tool_args = params.get("arguments", {})

        if tool_name == "list_doc_sources":
            res = list_doc_sources(category=tool_args.get("category", "ALL"))
            return {"jsonrpc": "2.0", "id": req_id, "result": {"content": [{"type": "text", "text": res}]}}

        if tool_name == "fetch_docs":
            res = fetch_docs(url=tool_args.get("url", ""), extract_links=tool_args.get("extract_links", True))
            return {"jsonrpc": "2.0", "id": req_id, "result": {"content": [{"type": "text", "text": res}]}}

        if tool_name == "search_doc_topics":
            res = search_doc_topics(query=tool_args.get("query", ""))
            return {"jsonrpc": "2.0", "id": req_id, "result": {"content": [{"type": "text", "text": res}]}}

        if tool_name == "get_control_point_guide":
            res = get_control_point_guide(control_point=tool_args.get("control_point", "ALL"))
            return {"jsonrpc": "2.0", "id": req_id, "result": {"content": [{"type": "text", "text": res}]}}

        if tool_name == "get_mmm_workflow_guide":
            res = get_mmm_workflow_guide(phase=tool_args.get("phase", "ALL"))
            return {"jsonrpc": "2.0", "id": req_id, "result": {"content": [{"type": "text", "text": res}]}}

        if tool_name == "calculate_bayesian_prior":
            res = calculate_bayesian_prior(
                experiment_type=tool_args.get("experiment_type", "geo_lift"),
                point_estimate=tool_args.get("point_estimate", 2.0),
                ci_lower=tool_args.get("ci_lower", 1.2),
                ci_upper=tool_args.get("ci_upper", 2.8)
            )
            return {"jsonrpc": "2.0", "id": req_id, "result": {"content": [{"type": "text", "text": res}]}}

        if tool_name == "audit_model_first_principles":
            res = audit_model_first_principles(config_json=tool_args.get("config_json", "{}"))
            return {"jsonrpc": "2.0", "id": req_id, "result": {"content": [{"type": "text", "text": res}]}}

        if tool_name == "synthesize_meridian_code":
            res = synthesize_meridian_code(
                pipeline_stage=tool_args.get("pipeline_stage", "FULL_PIPELINE"),
                config_json=tool_args.get("config_json", "{}")
            )
            return {"jsonrpc": "2.0", "id": req_id, "result": {"content": [{"type": "text", "text": res}]}}

        if tool_name == "generate_schema_template":
            res = generate_schema_template(
                n_weeks=tool_args.get("n_weeks", 104),
                n_geos=tool_args.get("n_geos", 1),
                n_channels=tool_args.get("n_channels", 3)
            )
            return {"jsonrpc": "2.0", "id": req_id, "result": {"content": [{"type": "text", "text": res}]}}

        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "error": {"code": -32601, "message": f"Tool '{tool_name}' not found"}
        }

    return {"jsonrpc": "2.0", "id": req_id, "result": {}}


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8080"))
    mode = os.environ.get("MCP_MODE", "stdio").lower()
    
    if mode == "sse" or "PORT" in os.environ:
        _log_structured("INFO", f"Starting Google Meridian MCP Server in SSE Mode on 0.0.0.0:{port}")
        import uvicorn
        from starlette.responses import JSONResponse, Response, PlainTextResponse

        sse_app = mcp.sse_app()

        async def main_app(scope, receive, send):
            if scope["type"] == "http":
                path = scope["path"]
                method = scope["method"]

                if method == "DELETE":
                    response = Response(status_code=204)
                    await response(scope, receive, send)
                    return

                if ".well-known" in path:
                    response = JSONResponse({"status": "no_auth_required"}, status_code=200)
                    await response(scope, receive, send)
                    return

                if path == "/health":
                    response = JSONResponse({
                        "status": "HEALTHY",
                        "uptime_seconds": round(time.time() - SERVER_START_TIME, 2),
                        "cache_items": len(list(CACHE_DIR.glob("*.md")))
                    }, status_code=200)
                    await response(scope, receive, send)
                    return

                if path == "/metrics":
                    response = Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
                    await response(scope, receive, send)
                    return

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

                if method == "POST":
                    try:
                        body_bytes = b""
                        while True:
                            message = await receive()
                            body_bytes += message.get("body", b"")
                            if not message.get("more_body", False):
                                break
                        
                        if body_bytes:
                            body_json = json.loads(body_bytes.decode("utf-8"))
                            jsonrpc_res = _handle_jsonrpc_request(body_json)
                            response = JSONResponse(jsonrpc_res, status_code=200)
                            await response(scope, receive, send)
                            return
                    except Exception as err:
                        _log_structured("WARNING", f"Direct POST fallback error: {str(err)}")

            await sse_app(scope, receive, send)

        uvicorn.run(main_app, host="0.0.0.0", port=port)
    else:
        mcp.run()
