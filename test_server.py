"""
Unit and Integration Tests for Google Meridian MCP Server.
"""

import unittest
import json
from doc_index import MERIDIAN_DOC_SOURCES, TOPIC_KEYWORDS
import server


class TestDocIndex(unittest.TestCase):

    def test_doc_sources_not_empty(self):
        """Ensure all documentation categories contain sources with valid titles and URLs."""
        self.assertGreater(len(MERIDIAN_DOC_SOURCES), 0)
        total_items = sum(len(items) for items in MERIDIAN_DOC_SOURCES.values())
        self.assertGreaterEqual(total_items, 600, "Master catalog should contain at least 600 items")
        for category, items in MERIDIAN_DOC_SOURCES.items():
            self.assertTrue(len(items) > 0, f"Category {category} is empty")
            for item in items:
                self.assertIn("title", item)
                self.assertIn("url", item)
                self.assertIn("description", item)
                self.assertTrue(item["url"].startswith("http"), f"Invalid URL: {item['url']}")

    def test_topic_keywords_mapping(self):
        """Ensure topic keywords map to valid documentation items."""
        self.assertIn("budget", TOPIC_KEYWORDS)
        self.assertIn("install", TOPIC_KEYWORDS)
        self.assertIn("causal", TOPIC_KEYWORDS)
        for keyword, items in TOPIC_KEYWORDS.items():
            self.assertTrue(len(items) > 0, f"Keyword '{keyword}' mapped to empty list")


class TestMCPServerTools(unittest.TestCase):

    def test_list_doc_sources_all(self):
        """Test list_doc_sources with default category 'ALL'."""
        result = server.list_doc_sources(category="ALL")
        self.assertIn("# Google Meridian Documentation Sources", result)
        self.assertIn("Category: OVERVIEW AND SETUP", result)
        self.assertIn("Category: API REFERENCE", result)
        self.assertIn("Category: CAUSAL INFERENCE THEORY", result)

    def test_list_doc_sources_filtered(self):
        """Test list_doc_sources with specific category filter."""
        result = server.list_doc_sources(category="PRE_MODELING")
        self.assertIn("Category: PRE MODELING", result)
        self.assertNotIn("Category: API REFERENCE", result)

    def test_search_doc_topics_matching(self):
        """Test search_doc_topics with matching keywords."""
        result = server.search_doc_topics(query="budget")
        self.assertIn("Topic Search Results for 'budget'", result)

    def test_search_doc_topics_fallback(self):
        """Test search_doc_topics fallback search."""
        result = server.search_doc_topics(query="causal")
        self.assertIn("Search Results for 'causal'", result)

    def test_search_doc_topics_no_match(self):
        """Test search_doc_topics when no match is found."""
        result = server.search_doc_topics(query="xyz123nonexistent")
        self.assertIn("No direct documentation match found", result)

    def test_url_allowed_domain_check(self):
        """Test domain security validation for fetch_docs."""
        self.assertTrue(server._is_url_allowed("https://developers.google.com/meridian/mmm"))
        self.assertTrue(server._is_url_allowed("https://github.com/google/meridian"))
        self.assertTrue(server._is_url_allowed("https://raw.githubusercontent.com/google/meridian/main/README.md"))
        self.assertFalse(server._is_url_allowed("https://unauthorized-domain.com/hack"))
        self.assertFalse(server._is_url_allowed("http://169.254.169.254/latest/meta-data/"))

    def test_fetch_docs_disallowed_domain(self):
        """Test fetch_docs error response for disallowed URLs."""
        result = server.fetch_docs(url="https://evil.com/payload")
        self.assertIn("Error: URL 'https://evil.com/payload' is not from an allowed domain", result)

    def test_parse_ipynb_cells(self):
        """Test Jupyter Notebook JSON parsing into Markdown."""
        sample_nb = {
            "cells": [
                {
                    "cell_type": "markdown",
                    "source": ["# Title Cell\n", "Intro text."]
                },
                {
                    "cell_type": "code",
                    "source": ["import meridian\n", "print('hello')"]
                }
            ]
        }
        rendered = server._parse_ipynb_cells(sample_nb)
        self.assertIn("# Title Cell", rendered)
        self.assertIn("```python\nimport meridian\nprint('hello')\n```", rendered)


class TestFirstPrinciplesDataScienceTools(unittest.TestCase):

    def test_get_control_point_guide(self):
        """Test get_control_point_guide for all control points and specific point."""
        res_all = server.get_control_point_guide("ALL")
        self.assertIn("Control Point 1: Data Inputs", res_all)
        self.assertIn("Control Point 5: Bayesian Prior Calibration", res_all)

        res_priors = server.get_control_point_guide("bayesian_priors")
        self.assertIn("Meridian Control Point Guide: BAYESIAN_PRIORS", res_priors)

    def test_get_mmm_workflow_guide(self):
        """Test get_mmm_workflow_guide for workflow phases and iteration loops."""
        res_wf = server.get_mmm_workflow_guide("ALL")
        self.assertIn("Phase 1: Data Alignment", res_wf)
        self.assertIn("Loop A: Technical Convergence Check", res_wf)
        self.assertIn("Loop C: Lift Test Alignment", res_wf)

        res_loop_a = server.get_mmm_workflow_guide("loop_a_convergence")
        self.assertIn("Loop A: Technical Convergence Check", res_loop_a)

    def test_calculate_bayesian_prior(self):
        """Test calculate_bayesian_prior math derivation and code generation."""
        res = server.calculate_bayesian_prior(
            experiment_type="geo_lift",
            point_estimate=2.0,
            ci_lower=1.2,
            ci_upper=2.8
        )
        self.assertIn("Calculated Meridian LogNormal Prior Parameters", res)
        self.assertIn("scale=", res)
        self.assertIn("loc=", res)

        # Invalid bounds test
        res_err = server.calculate_bayesian_prior(point_estimate=-1.0, ci_lower=1.0, ci_upper=2.0)
        self.assertIn("Error:", res_err)

    def test_audit_model_first_principles(self):
        """Test audit_model_first_principles for knot distance and prior SD risks."""
        config = json.dumps({"knot_distance_weeks": 2, "prior_sd": 1.5})
        audit = server.audit_model_first_principles(config)
        self.assertIn("CRITICAL: Knot distance (2 weeks) is too small", audit)
        self.assertIn("WARNING: Prior standard deviation (1.5) is too uninformative", audit)

    def test_run_eda_checks(self):
        """Test run_eda_checks output."""
        res = server.run_eda_checks()
        self.assertIn("VIFSpec", res)
        self.assertIn("DataParameterRatioArtifact", res)

    def test_run_model_review_checks(self):
        """Test run_model_review_checks output."""
        res = server.run_model_review_checks("ALL")
        self.assertIn("BayesianPPPCheck", res)
        self.assertIn("PriorPosteriorShiftCheck", res)

    def test_synthesize_meridian_code(self):
        """Test synthesize_meridian_code python output."""
        code_full = server.synthesize_meridian_code("FULL_PIPELINE")
        self.assertIn("from meridian.data import input_data", code_full)
        self.assertIn("from meridian.analysis import optimizer", code_full)

    def test_generate_schema_template(self):
        """Test generate_schema_template CSV generation."""
        csv_out = server.generate_schema_template(n_weeks=52, n_geos=1, n_channels=3)
        self.assertIn("time,geo,kpi,spend_channel_1,impressions_channel_1", csv_out)


if __name__ == "__main__":
    unittest.main()

