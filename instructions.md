# Google Meridian MCP Server Instructions

Use this MCP server to guide data scientists through creating, auditing, calibrating, and optimizing a proper **Google Meridian Marketing Mix Model (MMM)** built on **First Principles**, **Control Points**, **Workflow Loops**, and **Cloud-Agnostic Design**.

For detailed mathematical, statistical, and architectural foundations, refer to [FIRST_PRINCIPLES_MMM.md](FIRST_PRINCIPLES_MMM.md).

## The 4 Mandate Pillars

1. **Every Control Point**: Data Inputs, Confounders (DAG), Seasonality Knots, Adstock Decay, Hill Saturation, Bayesian Priors, MCMC Parameters, and Optimization Bounds.
2. **End-to-End Workflow & Iterations**: 5 Modeling Phases & 3 Iteration Loops (*Loop A: Technical Convergence $\rightarrow$ Loop B: Causal Plausibility $\rightarrow$ Loop C: Lift Calibration*).
3. **First Principles**: Grounded in causal identification, probability distribution math, NUTS sampling geometry, and KKT convex optimization.
4. **Platform Agnostic**: 100% portable, zero cloud lock-in. Runs locally, in Docker, or on any cloud (AWS, Azure, GCP, Railway, Render, etc.).

## Available Tools & Workflow

1. **`get_control_point_guide(control_point)`**:
   - Detailed mathematical derivations, formulas, parameters, and bounds for all 7 control points (`data_inputs`, `confounders_and_dag`, `adstock_decay`, `hill_saturation`, `bayesian_priors`, `mcmc_diagnostics`, `optimization_bounds`).

2. **`get_mmm_workflow_guide(phase)`**:
   - Step-by-step decision trees and iteration rules for the 5 modeling phases and 3 iteration loops.

3. **`calculate_bayesian_prior(experiment_type, point_estimate, ci_lower, ci_upper)`**:
   - Solves probability equations to convert 95% Confidence Intervals from Lift Tests into Meridian LogNormal ($\mu, \sigma$) or Beta ($\alpha, \beta$) prior parameters.

4. **`audit_model_first_principles(config_json)`**:
   - Diagnostic auditor evaluating channel identifiability, knot density, prior variance, and Hill parameter bounds.

5. **`synthesize_meridian_code(pipeline_stage, config_json)`**:
   - Generates clean, portable Python code implementing Google Meridian's `InputData`, `ModelSpec`, `PriorCalibration`, `fit()`, and `BudgetOptimizer`.

6. **`generate_schema_template(n_weeks, n_geos, n_channels)`**:
   - Synthesizes benchmarking datasets matching Meridian's input schema.

7. **`list_doc_sources(category)`**, **`search_doc_topics(query)`**, **`fetch_docs(url)`**:
   - Knowledge base tools for searching and fetching official Meridian guides, API specs, and GitHub code.
