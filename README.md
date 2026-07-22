# Google Meridian MCP Server (`google-meridian-mcp`)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![MCP Standard](https://img.shields.io/badge/MCP-Standard-green.svg)](https://modelcontextprotocol.io)

An open-source Model Context Protocol (MCP) server for **Google Meridian** (Marketing Mix Modeling). It provides AI assistants (like Cursor, Claude Desktop, and Gemini / Antigravity) with structured access to official guides, API references, topic searching, and GitHub source code.

---

## ⚡ Quick Connect (Remote SSE Mode)

You can use the live public remote MCP server without installing anything locally! Simply add this to your IDE's `mcp_config.json`:

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

## ✨ Features

- **Multi-Category Indexing**: Complete hierarchical index across User Guides, Pre-Modeling, Model Specification & Fitting, Post-Modeling & Optimization, Advanced Modeling, API References, and GitHub Code.
- **Dynamic HTML ➔ Markdown Parser**: Converts Google Developer HTML documentation pages into clean, boilerplate-free Markdown.
- **GitHub & Jupyter Notebook Parser**: Renders raw `.py` code files and `.ipynb` Jupyter demo notebooks into readable Markdown.
- **Topic Search Engine (`search_doc_topics`)**: Instant keyword/topic matching for concepts like *Adstock*, *Hill curves*, *NUTS sampling*, *Prior calibration*, and *BudgetOptimizer*.
- **Observability & Security**: Built-in Prometheus metrics (`/metrics`), structured Cloud logging, and IP rate limiting for public cost protection.

---

## 🛠️ Available Tools

| Tool | Parameters | Description |
| :--- | :--- | :--- |
| `list_doc_sources` | `category: str = "ALL"` | Lists documentation sources filtered by category. |
| `fetch_docs` | `url: str, extract_links: bool = True` | Fetches, cleans, and converts doc pages / GitHub code to Markdown. |
| `search_doc_topics` | `query: str` | Searches Meridian topics and returns direct matching URLs. |

---

## 💻 Local Setup & Running

### Option A: Python Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Run server
python server.py
```

Local `mcp_config.json`:
```json
{
  "mcpServers": {
    "google-meridian-mcp": {
      "command": "python",
      "args": [
        "path/to/google-meridian-mcp/server.py"
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

## 🧪 Testing

Run the automated unit test suite:

```bash
python -m unittest test_server.py -v
```

---

## 📄 License

[MIT License](LICENSE). Open source and free for the community.
