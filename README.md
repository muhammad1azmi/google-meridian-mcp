# Google Meridian MCP Server (`google-meridian-mcp`)

A high-performance Model Context Protocol (MCP) server for **Google Meridian** (Marketing Mix Modeling), providing AI assistants with structured access to official guides, API references, topic searching, and GitHub source code.

---

## Features

- **Multi-Category Indexing**: Complete hierarchical index across User Guides, Pre-Modeling, Model Specification & Fitting, Post-Modeling & Optimization, Advanced Modeling, API References, and GitHub Code.
- **Dynamic HTML ➔ Markdown Parser**: Converts Google Developer HTML documentation pages into clean, boilerplate-free Markdown.
- **GitHub & Jupyter Notebook Parser**: Renders raw `.py` code files and `.ipynb` Jupyter demo notebooks into readable Markdown.
- **Topic Search Engine (`search_doc_topics`)**: Instant keyword/topic matching for concepts like *Adstock*, *Hill curves*, *NUTS sampling*, *Prior calibration*, and *BudgetOptimizer*.
- **Local Disk Cache**: Fast response times and offline reliability via `.cache/`.

---

## Available Tools

| Tool | Parameters | Description |
| :--- | :--- | :--- |
| `list_doc_sources` | `category: str = "ALL"` | Lists documentation sources filtered by category. |
| `fetch_docs` | `url: str, extract_links: bool = True` | Fetches, cleans, and converts doc pages / GitHub code to Markdown. |
| `search_doc_topics` | `query: str` | Searches Meridian topics and returns direct matching URLs. |

---

## Usage & IDE Integration

### Local Usage (Stdio Mode)

To run locally with Python:

```bash
python server.py
```

Add to your IDE's `mcp_config.json`:

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

---

## License

MIT License. Open source and free for developer use.
