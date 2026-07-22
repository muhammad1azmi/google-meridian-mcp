# Google Meridian MCP Server Instructions

Use this MCP server to explore, search, and read official Google Meridian documentation, Python API references, user guides, and GitHub source code.

## Available Tools & Workflow

1. **`list_doc_sources(category="ALL")`**:
   - Call this tool first to discover the full tree of Meridian documentation.
   - Categories available: `OVERVIEW_AND_SETUP`, `PRE_MODELING`, `MODELING_AND_FITTING`, `POST_MODELING_AND_OPTIMIZATION`, `ADVANCED_MODELING`, `API_REFERENCE`, `GITHUB_REPOSITORY`.

2. **`search_doc_topics(query)`**:
   - Use this tool to search for specific topics, concepts, or components (e.g. `budget optimizer`, `adstock`, `priors`, `NUTS sampling`, `geo level data`, `R-hat diagnostics`).

3. **`fetch_docs(url)`**:
   - Pass any URL returned by `list_doc_sources` or `search_doc_topics` to retrieve the clean Markdown text.
   - Works on Google Developer documentation pages (`developers.google.com/meridian`), GitHub Python source code (`spec.py`, `optimizer.py`), and Jupyter Notebooks (`.ipynb`).
