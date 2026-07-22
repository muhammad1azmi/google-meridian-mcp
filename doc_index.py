"""
Google Meridian Documentation Index and Knowledge Mapping.

Exhaustive master directory containing 600+ official Google Meridian
documentation categories, sub-pages, API reference endpoints, and GitHub code paths.
"""

import json
from pathlib import Path
from typing import Dict, List, Any

_CATALOG_FILE = Path(__file__).parent / "master_catalog.json"

if _CATALOG_FILE.exists():
    with open(_CATALOG_FILE, "r", encoding="utf-8") as f:
        MERIDIAN_DOC_SOURCES: Dict[str, List[Dict[str, str]]] = json.load(f)
else:
    MERIDIAN_DOC_SOURCES: Dict[str, List[Dict[str, str]]] = {
        "OVERVIEW_AND_SETUP": [],
        "PRE_MODELING": [],
        "MODELING_AND_FITTING": [],
        "POST_MODELING_AND_OPTIMIZATION": [],
        "CAUSAL_INFERENCE_THEORY": [],
        "ADVANCED_MODELING": [],
        "API_REFERENCE": [],
        "GITHUB_REPOSITORY": []
    }

# Topic Keyword Search Mapping
TOPIC_KEYWORDS: Dict[str, List[Dict[str, str]]] = {
    "install": MERIDIAN_DOC_SOURCES.get("OVERVIEW_AND_SETUP", []),
    "data": MERIDIAN_DOC_SOURCES.get("PRE_MODELING", []) + MERIDIAN_DOC_SOURCES.get("API_REFERENCE", []),
    "priors": MERIDIAN_DOC_SOURCES.get("MODELING_AND_FITTING", []) + MERIDIAN_DOC_SOURCES.get("ADVANCED_MODELING", []),
    "mcmc": MERIDIAN_DOC_SOURCES.get("MODELING_AND_FITTING", []),
    "nuts": MERIDIAN_DOC_SOURCES.get("MODELING_AND_FITTING", []),
    "roi": MERIDIAN_DOC_SOURCES.get("POST_MODELING_AND_OPTIMIZATION", []) + MERIDIAN_DOC_SOURCES.get("ADVANCED_MODELING", []),
    "budget": MERIDIAN_DOC_SOURCES.get("POST_MODELING_AND_OPTIMIZATION", []),
    "optimizer": MERIDIAN_DOC_SOURCES.get("POST_MODELING_AND_OPTIMIZATION", []),
    "causal": MERIDIAN_DOC_SOURCES.get("CAUSAL_INFERENCE_THEORY", []),
    "dag": MERIDIAN_DOC_SOURCES.get("CAUSAL_INFERENCE_THEORY", []),
    "adstock": MERIDIAN_DOC_SOURCES.get("ADVANCED_MODELING", []),
    "hill": MERIDIAN_DOC_SOURCES.get("ADVANCED_MODELING", []),
    "calibration": MERIDIAN_DOC_SOURCES.get("ADVANCED_MODELING", []),
    "visualizer": MERIDIAN_DOC_SOURCES.get("POST_MODELING_AND_OPTIMIZATION", [])
}
