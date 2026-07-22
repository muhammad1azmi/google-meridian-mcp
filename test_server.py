"""
Unit and Integration Tests for Google Meridian MCP Server.
"""

import unittest
from doc_index import MERIDIAN_DOC_SOURCES, TOPIC_KEYWORDS
import server


class TestDocIndex(unittest.TestCase):

    def test_doc_sources_not_empty(self):
        """Ensure all documentation categories contain sources with valid titles and URLs."""
        self.assertGreater(len(MERIDIAN_DOC_SOURCES), 0)
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
        self.assertIn("modelspec", TOPIC_KEYWORDS)
        for keyword, items in TOPIC_KEYWORDS.items():
            self.assertTrue(len(items) > 0, f"Keyword '{keyword}' mapped to empty list")


class TestMCPServerTools(unittest.TestCase):

    def test_list_doc_sources_all(self):
        """Test list_doc_sources with default category 'ALL'."""
        result = server.list_doc_sources(category="ALL")
        self.assertIn("# Google Meridian Documentation Sources", result)
        self.assertIn("Category: OVERVIEW AND SETUP", result)
        self.assertIn("Category: API REFERENCE", result)

    def test_list_doc_sources_filtered(self):
        """Test list_doc_sources with specific category filter."""
        result = server.list_doc_sources(category="PRE_MODELING")
        self.assertIn("Category: PRE MODELING", result)
        self.assertNotIn("Category: API REFERENCE", result)

    def test_search_doc_topics_matching(self):
        """Test search_doc_topics with matching keywords."""
        result = server.search_doc_topics(query="budget optimizer")
        self.assertIn("Topic Search Results for 'budget optimizer'", result)
        self.assertIn("Budget Optimizer", result)

    def test_search_doc_topics_fallback(self):
        """Test search_doc_topics fallback search."""
        result = server.search_doc_topics(query="NUTS")
        self.assertIn("MCMC Sampling & Model Fit", result)

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


if __name__ == "__main__":
    unittest.main()
