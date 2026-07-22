"""
Google Meridian Documentation Index and Knowledge Mapping.

This module provides structured access to all official Google Meridian
documentation categories, sub-pages, API reference endpoints, GitHub code paths,
and topic search maps.
"""

from typing import Dict, List, Any

# Master Directory of Documentation Sources grouped by Category
MERIDIAN_DOC_SOURCES: Dict[str, List[Dict[str, str]]] = {
    "OVERVIEW_AND_SETUP": [
        {
            "title": "Meridian Framework Overview",
            "url": "https://developers.google.com/meridian/mmm",
            "description": "High-level overview of Google Meridian Bayesian Marketing Mix Modeling framework."
        },
        {
            "title": "Install Meridian",
            "url": "https://developers.google.com/meridian/docs/user-guide/installing",
            "description": "System requirements (Python 3.11-3.12, GPU/CUDA) and installation commands."
        },
        {
            "title": "Getting Started Notebook (Colab)",
            "url": "https://raw.githubusercontent.com/google/meridian/main/demo/Meridian_Getting_Started.ipynb",
            "description": "End-to-end Python demo walkthrough: loading data, fitting model, running diagnostics, and budget optimization."
        }
    ],
    "PRE_MODELING": [
        {
            "title": "Pre-Modeling Introduction",
            "url": "https://developers.google.com/meridian/docs/pre-modeling/intro",
            "description": "Overview of data preparation, KPI selection, and channel definition."
        },
        {
            "title": "Data Requirements & Schema",
            "url": "https://developers.google.com/meridian/docs/pre-modeling/data-requirements",
            "description": "Specification for input CSV/DataFrame format: time, KPI, spend, impressions/GRP, controls."
        },
        {
            "title": "Geo vs National Modeling",
            "url": "https://developers.google.com/meridian/docs/pre-modeling/geo-vs-national",
            "description": "Guidance on choosing between geo-level and national-level granularity."
        },
        {
            "title": "Media, Organic & Control Variables",
            "url": "https://developers.google.com/meridian/docs/pre-modeling/variables",
            "description": "Selecting paid media channels, organic brand variables, and non-marketing controls."
        }
    ],
    "MODELING_AND_FITTING": [
        {
            "title": "ModelSpec Configuration",
            "url": "https://developers.google.com/meridian/docs/modeling/model-spec",
            "description": "Configuring ModelSpec: media channels, knots, holdout samples, and control variables."
        },
        {
            "title": "Bayesian Priors Setup",
            "url": "https://developers.google.com/meridian/docs/modeling/priors",
            "description": "Defining ROI priors, saturation priors, hill curves, and custom prior distributions."
        },
        {
            "title": "MCMC Sampling & Model Fit",
            "url": "https://developers.google.com/meridian/docs/modeling/model-fit",
            "description": "Fitting Meridian model using No-U-Turn Sampler (NUTS) MCMC."
        },
        {
            "title": "Model Diagnostics & Convergence",
            "url": "https://developers.google.com/meridian/docs/modeling/diagnostics",
            "description": "Evaluating MCMC convergence (R-hat, effective sample size, posterior predictive checks)."
        }
    ],
    "POST_MODELING_AND_OPTIMIZATION": [
        {
            "title": "Post-Modeling & ROI Estimation",
            "url": "https://developers.google.com/meridian/docs/post-modeling/roi",
            "description": "Analyzing posterior ROI estimates, incremental KPI attribution, and channel responsiveness."
        },
        {
            "title": "Budget Optimizer & Response Curves",
            "url": "https://developers.google.com/meridian/docs/post-modeling/budget-optimization",
            "description": "Using BudgetOptimizer to calculate optimal media spend allocation across channels."
        },
        {
            "title": "Meridian Scenario Planner",
            "url": "https://developers.google.com/meridian/docs/scenario-planning/meridian-scenario-planner",
            "description": "Interactive scenario planner guide for marketing budget simulation."
        },
        {
            "title": "Visualizer & Reporting",
            "url": "https://developers.google.com/meridian/docs/post-modeling/visualizer",
            "description": "Generating visual reports for ROI, saturation curves, and media spend efficiency."
        }
    ],
    "ADVANCED_MODELING": [
        {
            "title": "Advanced Modeling Introduction",
            "url": "https://developers.google.com/meridian/docs/advanced-modeling/intro",
            "description": "Advanced topics in Meridian modeling."
        },
        {
            "title": "Experiment Calibration & Prior Integration",
            "url": "https://developers.google.com/meridian/docs/advanced-modeling/priors-calibration",
            "description": "Calibrating Bayesian MMM priors using geo-experiment incrementality test results."
        },
        {
            "title": "Custom Transformations (Adstock / Hill)",
            "url": "https://developers.google.com/meridian/docs/advanced-modeling/transformations",
            "description": "Customizing media adstock decay and Hill saturation functions."
        }
    ],
    "API_REFERENCE": [
        {
            "title": "Meridian Core API Root",
            "url": "https://developers.google.com/meridian/reference/api/meridian",
            "description": "Complete Python API reference for Google Meridian."
        },
        {
            "title": "meridian.model Module",
            "url": "https://developers.google.com/meridian/reference/api/meridian/model",
            "description": "API documentation for ModelSpec and Meridian model classes."
        },
        {
            "title": "meridian.data Module",
            "url": "https://developers.google.com/meridian/reference/api/meridian/data",
            "description": "API documentation for InputData, DataFetcher, and dataset validation classes."
        },
        {
            "title": "meridian.analysis Module",
            "url": "https://developers.google.com/meridian/reference/api/meridian/analysis",
            "description": "API documentation for Analyzer, BudgetOptimizer, and scenario optimization."
        },
        {
            "title": "meridian.visualizer Module",
            "url": "https://developers.google.com/meridian/reference/api/meridian/visualizer",
            "description": "API documentation for plotting and visualization utilities."
        }
    ],
    "GITHUB_REPOSITORY": [
        {
            "title": "Google Meridian GitHub Repository Root",
            "url": "https://github.com/google/meridian",
            "description": "Official open-source GitHub repository."
        },
        {
            "title": "Meridian Python Code Tree",
            "url": "https://github.com/google/meridian/tree/main/meridian",
            "description": "Directory of core Python source code files."
        },
        {
            "title": "meridian/model/spec.py (Raw Python)",
            "url": "https://raw.githubusercontent.com/google/meridian/main/meridian/model/spec.py",
            "description": "Raw Python source implementation of ModelSpec."
        },
        {
            "title": "meridian/analysis/budget_optimizer.py (Raw Python)",
            "url": "https://raw.githubusercontent.com/google/meridian/main/meridian/analysis/budget_optimizer.py",
            "description": "Raw Python source implementation of BudgetOptimizer."
        }
    ]
}

# Topic Keyword Search Mapping
TOPIC_KEYWORDS: Dict[str, List[Dict[str, str]]] = {
    "install": [
        MERIDIAN_DOC_SOURCES["OVERVIEW_AND_SETUP"][1]
    ],
    "pip": [
        MERIDIAN_DOC_SOURCES["OVERVIEW_AND_SETUP"][1]
    ],
    "gpu": [
        MERIDIAN_DOC_SOURCES["OVERVIEW_AND_SETUP"][1]
    ],
    "cuda": [
        MERIDIAN_DOC_SOURCES["OVERVIEW_AND_SETUP"][1]
    ],
    "notebook": [
        MERIDIAN_DOC_SOURCES["OVERVIEW_AND_SETUP"][2]
    ],
    "colab": [
        MERIDIAN_DOC_SOURCES["OVERVIEW_AND_SETUP"][2]
    ],
    "getting started": [
        MERIDIAN_DOC_SOURCES["OVERVIEW_AND_SETUP"][0],
        MERIDIAN_DOC_SOURCES["OVERVIEW_AND_SETUP"][2]
    ],
    "data": [
        MERIDIAN_DOC_SOURCES["PRE_MODELING"][1],
        MERIDIAN_DOC_SOURCES["API_REFERENCE"][2]
    ],
    "geo": [
        MERIDIAN_DOC_SOURCES["PRE_MODELING"][2],
        MERIDIAN_DOC_SOURCES["ADVANCED_MODELING"][1]
    ],
    "modelspec": [
        MERIDIAN_DOC_SOURCES["MODELING_AND_FITTING"][0],
        MERIDIAN_DOC_SOURCES["API_REFERENCE"][1],
        MERIDIAN_DOC_SOURCES["GITHUB_REPOSITORY"][2]
    ],
    "priors": [
        MERIDIAN_DOC_SOURCES["MODELING_AND_FITTING"][1],
        MERIDIAN_DOC_SOURCES["ADVANCED_MODELING"][1]
    ],
    "mcmc": [
        MERIDIAN_DOC_SOURCES["MODELING_AND_FITTING"][2],
        MERIDIAN_DOC_SOURCES["MODELING_AND_FITTING"][3]
    ],
    "nuts": [
        MERIDIAN_DOC_SOURCES["MODELING_AND_FITTING"][2]
    ],
    "diagnostics": [
        MERIDIAN_DOC_SOURCES["MODELING_AND_FITTING"][3]
    ],
    "r-hat": [
        MERIDIAN_DOC_SOURCES["MODELING_AND_FITTING"][3]
    ],
    "roi": [
        MERIDIAN_DOC_SOURCES["POST_MODELING_AND_OPTIMIZATION"][0],
        MERIDIAN_DOC_SOURCES["POST_MODELING_AND_OPTIMIZATION"][3]
    ],
    "budget": [
        MERIDIAN_DOC_SOURCES["POST_MODELING_AND_OPTIMIZATION"][1],
        MERIDIAN_DOC_SOURCES["POST_MODELING_AND_OPTIMIZATION"][2],
        MERIDIAN_DOC_SOURCES["API_REFERENCE"][3],
        MERIDIAN_DOC_SOURCES["GITHUB_REPOSITORY"][3]
    ],
    "optimizer": [
        MERIDIAN_DOC_SOURCES["POST_MODELING_AND_OPTIMIZATION"][1],
        MERIDIAN_DOC_SOURCES["API_REFERENCE"][3],
        MERIDIAN_DOC_SOURCES["GITHUB_REPOSITORY"][3]
    ],
    "adstock": [
        MERIDIAN_DOC_SOURCES["ADVANCED_MODELING"][2]
    ],
    "hill": [
        MERIDIAN_DOC_SOURCES["ADVANCED_MODELING"][2]
    ],
    "calibration": [
        MERIDIAN_DOC_SOURCES["ADVANCED_MODELING"][1]
    ],
    "visualizer": [
        MERIDIAN_DOC_SOURCES["POST_MODELING_AND_OPTIMIZATION"][3],
        MERIDIAN_DOC_SOURCES["API_REFERENCE"][4]
    ]
}
