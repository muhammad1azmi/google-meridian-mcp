import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";

const MERIDIAN_DOC_SOURCES = {
  OVERVIEW_AND_SETUP: [
    {
      title: "Meridian Framework Overview",
      url: "https://developers.google.com/meridian/mmm",
      description: "High-level overview of Google Meridian Bayesian Marketing Mix Modeling framework."
    },
    {
      title: "Install Meridian",
      url: "https://developers.google.com/meridian/docs/user-guide/installing",
      description: "System requirements (Python 3.11-3.12, GPU/CUDA) and installation commands."
    },
    {
      title: "Getting Started Notebook (Colab)",
      url: "https://raw.githubusercontent.com/google/meridian/main/demo/Meridian_Getting_Started.ipynb",
      description: "End-to-end Python demo walkthrough: loading data, fitting model, running diagnostics, and budget optimization."
    }
  ],
  PRE_MODELING: [
    {
      title: "Pre-Modeling Introduction",
      url: "https://developers.google.com/meridian/docs/pre-modeling/intro",
      description: "Overview of data preparation, KPI selection, and channel definition."
    },
    {
      title: "Data Requirements & Schema",
      url: "https://developers.google.com/meridian/docs/pre-modeling/data-requirements",
      description: "Specification for input CSV/DataFrame format: time, KPI, spend, impressions/GRP, controls."
    },
    {
      title: "Geo vs National Modeling",
      url: "https://developers.google.com/meridian/docs/pre-modeling/geo-vs-national",
      description: "Guidance on choosing between geo-level and national-level granularity."
    }
  ],
  MODELING_AND_FITTING: [
    {
      title: "ModelSpec Configuration",
      url: "https://developers.google.com/meridian/docs/modeling/model-spec",
      description: "Configuring ModelSpec: media channels, knots, holdout samples, and control variables."
    },
    {
      title: "Bayesian Priors Setup",
      url: "https://developers.google.com/meridian/docs/modeling/priors",
      description: "Defining ROI priors, saturation priors, hill curves, and custom prior distributions."
    },
    {
      title: "MCMC Sampling & Model Fit",
      url: "https://developers.google.com/meridian/docs/modeling/model-fit",
      description: "Fitting Meridian model using No-U-Turn Sampler (NUTS) MCMC."
    }
  ],
  POST_MODELING_AND_OPTIMIZATION: [
    {
      title: "Post-Modeling & ROI Estimation",
      url: "https://developers.google.com/meridian/docs/post-modeling/roi",
      description: "Analyzing posterior ROI estimates, incremental KPI attribution, and channel responsiveness."
    },
    {
      title: "Budget Optimizer & Response Curves",
      url: "https://developers.google.com/meridian/docs/post-modeling/budget-optimization",
      description: "Using BudgetOptimizer to calculate optimal media spend allocation across channels."
    }
  ],
  API_REFERENCE: [
    {
      title: "Meridian Core API Root",
      url: "https://developers.google.com/meridian/reference/api/meridian",
      description: "Complete Python API reference for Google Meridian."
    },
    {
      title: "meridian.model Module",
      url: "https://developers.google.com/meridian/reference/api/meridian/model",
      description: "API documentation for ModelSpec and Meridian model classes."
    },
    {
      title: "meridian.analysis Module",
      url: "https://developers.google.com/meridian/reference/api/meridian/analysis",
      description: "API documentation for Analyzer, BudgetOptimizer, and scenario optimization."
    }
  ],
  GITHUB_REPOSITORY: [
    {
      title: "Google Meridian GitHub Repository Root",
      url: "https://github.com/google/meridian",
      description: "Official open-source GitHub repository."
    },
    {
      title: "meridian/model/spec.py (Raw Python)",
      url: "https://raw.githubusercontent.com/google/meridian/main/meridian/model/spec.py",
      description: "Raw Python source implementation of ModelSpec."
    }
  ]
};

const server = new Server(
  {
    name: "google-meridian-mcp",
    version: "1.0.0",
  },
  {
    capabilities: {
      tools: {},
    },
  }
);

server.setRequestHandler(ListToolsRequestSchema, async () => {
  return {
    tools: [
      {
        name: "list_doc_sources",
        description: "List all available Google Meridian documentation sources, user guides, API references, and GitHub repository links.",
        inputSchema: {
          type: "object",
          properties: {
            category: {
              type: "string",
              description: "Category filter (ALL, OVERVIEW_AND_SETUP, PRE_MODELING, MODELING_AND_FITTING, POST_MODELING_AND_OPTIMIZATION, API_REFERENCE, GITHUB_REPOSITORY)",
              default: "ALL"
            }
          }
        }
      },
      {
        name: "search_doc_topics",
        description: "Search Google Meridian documentation by topic or keyword (e.g., 'adstock', 'priors', 'budget optimizer', 'NUTS', 'R-hat').",
        inputSchema: {
          type: "object",
          properties: {
            query: {
              type: "string",
              description: "Keyword or topic to search for."
            }
          },
          required: ["query"]
        }
      },
      {
        name: "fetch_docs",
        description: "Fetch and parse Google Meridian documentation or code into clean Markdown.",
        inputSchema: {
          type: "object",
          properties: {
            url: {
              type: "string",
              description: "The URL to fetch documentation from."
            }
          },
          required: ["url"]
        }
      }
    ]
  };
});

server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;

  if (name === "list_doc_sources") {
    const category = (args?.category || "ALL").toUpperCase();
    let text = "# Google Meridian Documentation Sources\n\n";

    for (const [cat, items] of Object.entries(MERIDIAN_DOC_SOURCES)) {
      if (category === "ALL" || category === cat) {
        text += `## Category: ${cat.replace(/_/g, " ")}\n`;
        for (const item of items) {
          text += `- **${item.title}**\n  - URL: ${item.url}\n  - Summary: ${item.description}\n\n`;
        }
      }
    }
    return { content: [{ type: "text", text }] };
  }

  if (name === "search_doc_topics") {
    const query = (args?.query || "").toLowerCase();
    let matches = [];

    for (const [cat, items] of Object.entries(MERIDIAN_DOC_SOURCES)) {
      for (const item of items) {
        if (item.title.toLowerCase().includes(query) || item.description.toLowerCase().includes(query)) {
          matches.push(item);
        }
      }
    }

    if (matches.length === 0) {
      return { content: [{ type: "text", text: `No direct matches found for topic '${query}'. Try searching for terms like 'data', 'priors', 'budget', 'install', or 'optimizer'.` }] };
    }

    let text = `# Search Results for '${query}'\n\n`;
    for (const item of matches) {
      text += `- **${item.title}**\n  - URL: ${item.url}\n  - Summary: ${item.description}\n\n`;
    }
    return { content: [{ type: "text", text }] };
  }

  if (name === "fetch_docs") {
    const url = args?.url;
    try {
      const res = await fetch(url);
      const htmlOrText = await res.text();
      return { content: [{ type: "text", text: `# Content for ${url}\n\n${htmlOrText.slice(0, 5000)}` }] };
    } catch (err) {
      return { content: [{ type: "text", text: `Error fetching URL: ${err.message}` }] };
    }
  }

  throw new Error(`Unknown tool: ${name}`);
});

async function run() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
}

run().catch(console.error);
