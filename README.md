# Google Meridian MCP Server (`google-meridian-mcp`)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Node.js 18+](https://img.shields.io/badge/node.js-18+-green.svg)](https://nodejs.org/)
[![MCP Standard](https://img.shields.io/badge/MCP-Standard-green.svg)](https://modelcontextprotocol.io)

A **Cloud-Agnostic, First-Principles Model Context Protocol (MCP) server** for **Google Meridian** and Marketing Mix Modeling (MMM). 

It empowers data scientists and AI assistants (Cursor, Claude Desktop, Antigravity) to create, audit, calibrate, and optimize mathematically sound, causally valid Marketing Mix Models with zero cloud vendor lock-in.

📖 **Source of Truth**: Read [FIRST_PRINCIPLES_MMM.md](FIRST_PRINCIPLES_MMM.md) for full mathematical derivations, causal DAG rules, control points, and workflow iteration loops.

---

## 🏛️ The 4 Mandate Pillars

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│ 1. EVERY CONTROL POINT   │ Covers Data Inputs, Controls/DAG, Baseline, Adstock,        │
│                          │ Hill Saturation, Bayesian Priors, MCMC, Optimization.       │
├──────────────────────────┼─────────────────────────────────────────────────────────────┤
│ 2. END-TO-END WORKFLOW   │ Guides the 5 phases & 3 iteration loops (Convergence        │
│                          │ Diagnostics ➔ Causal Plausibility ➔ Lift Calibration).      │
├──────────────────────────┼─────────────────────────────────────────────────────────────┤
│ 3. FIRST PRINCIPLES      │ Grounded in causal inference, probability theory, HMC/NUTS  │
│                          │ sampling geometry, and convex optimization math.            │
├──────────────────────────┼─────────────────────────────────────────────────────────────┤
│ 4. PLATFORM AGNOSTIC     │ 100% portable with zero cloud vendor lock-in. Runs locally, │
│                          │ in Docker, or on AWS, Azure, GCP, Railway, Render, etc.     │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 🛠️ Complete MCP Tool Suite (9 Tools)

| Category | Tool | Parameters | Description |
| :--- | :--- | :--- | :--- |
| **Control Points** | `get_control_point_guide` | `control_point: str` | Operational parameters, math formulas, and recommended bounds for all 7 control points. |
| **Workflow** | `get_mmm_workflow_guide` | `phase: str` | Decision trees and iteration rules for the 5 modeling phases & 3 iteration loops. |
| **Prior Math Engine** | `calculate_bayesian_prior` | `point_estimate, ci_lower, ci_upper` | Converts 95% CIs from Lift Tests into exact Meridian LogNormal ($\mu, \sigma$) prior parameters. |
| **Spec Auditor** | `audit_model_first_principles` | `config_json: str` | Audits model specs for identifiability, knot density, prior variance, and Hill parameter bounds. |
| **Code Synthesizer** | `synthesize_meridian_code` | `pipeline_stage: str` | Generates clean, portable, cloud-agnostic Python code for Google Meridian pipelines. |
| **Data Utility** | `generate_schema_template` | `n_weeks, n_geos, n_channels` | Generates synthetic CSV schema templates matching Meridian's input format. |
| **Documentation** | `list_doc_sources` | `category: str` | Lists documentation sources filtered by category. |
| **Documentation** | `fetch_docs` | `url: str` | Fetches and parses documentation pages/GitHub code to Markdown. |
| **Documentation** | `search_doc_topics` | `query: str` | Searches Meridian topic index (Adstock, Hill curves, NUTS, Priors, etc.). |

---

## ⚡ Quick Connect (Remote SSE Mode)

Add this to your IDE's `mcp_config.json`:

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

## 💻 Local Setup & Running

### Option A: Python FastMCP Setup (Recommended)
```bash
# Install dependencies
pip install -r requirements.txt

# Run server in stdio mode
python server.py
```

`mcp_config.json`:
```json
{
  "mcpServers": {
    "google-meridian-mcp": {
      "command": "python",
      "args": [
        "C:/path/to/google-meridian-mcp/server.py"
      ]
    }
  }
}
```

### Option B: Node.js Setup
```bash
npm install
npm start
```

---

## 📄 License

[MIT License](LICENSE). Open source and free for the community.
