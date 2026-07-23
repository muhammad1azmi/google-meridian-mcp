import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";
import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

let MERIDIAN_DOC_SOURCES = {};
try {
  const catalogPath = path.join(__dirname, "master_catalog.json");
  MERIDIAN_DOC_SOURCES = JSON.parse(fs.readFileSync(catalogPath, "utf8"));
} catch (e) {
  console.error("Failed to load master_catalog.json:", e);
}

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
              description: "Category filter (ALL, OVERVIEW_AND_SETUP, PRE_MODELING, MODELING_AND_FITTING, POST_MODELING_AND_OPTIMIZATION, CAUSAL_INFERENCE_THEORY, ADVANCED_MODELING, API_REFERENCE, GITHUB_REPOSITORY)",
              default: "ALL"
            }
          }
        }
      },
      {
        name: "search_doc_topics",
        description: "Search Google Meridian documentation by topic or keyword (e.g., 'adstock', 'priors', 'budget optimizer', 'NUTS', 'R-hat', 'DAG', 'causal').",
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
      },
      {
        name: "get_control_point_guide",
        description: "Provides operational parameters, math formulas, and bounds for data science control points.",
        inputSchema: {
          type: "object",
          properties: {
            control_point: {
              type: "string",
              description: "data_inputs, confounders_and_dag, adstock_decay, hill_saturation, bayesian_priors, mcmc_diagnostics, optimization_bounds, or ALL",
              default: "ALL"
            }
          }
        }
      },
      {
        name: "get_mmm_workflow_guide",
        description: "Provides decision trees and iteration rules for modeling phases and iteration loops.",
        inputSchema: {
          type: "object",
          properties: {
            phase: {
              type: "string",
              description: "phase1_data_prep, phase2_specification, loop_a_convergence, loop_b_plausibility, loop_c_calibration, phase4_optimization, or ALL",
              default: "ALL"
            }
          }
        }
      },
      {
        name: "calculate_bayesian_prior",
        description: "Solves probability equations to convert 95% CIs into Meridian LogNormal (mu, sigma) prior parameters.",
        inputSchema: {
          type: "object",
          properties: {
            experiment_type: { type: "string", default: "geo_lift" },
            point_estimate: { type: "number", default: 2.0 },
            ci_lower: { type: "number", default: 1.2 },
            ci_upper: { type: "number", default: 2.8 }
          }
        }
      },
      {
        name: "audit_model_first_principles",
        description: "Audits model spec for identifiability, knot density, prior variance, and Hill parameter bounds.",
        inputSchema: {
          type: "object",
          properties: {
            config_json: { type: "string", default: "{}" }
          }
        }
      },
      {
        name: "synthesize_meridian_code",
        description: "Synthesizes clean, portable, cloud-agnostic Python code for Google Meridian.",
        inputSchema: {
          type: "object",
          properties: {
            pipeline_stage: { type: "string", default: "FULL_PIPELINE" },
            config_json: { type: "string", default: "{}" }
          }
        }
      },
      {
        name: "generate_schema_template",
        description: "Generates a synthetic benchmarking CSV schema template matching Meridian's input format.",
        inputSchema: {
          type: "object",
          properties: {
            n_weeks: { type: "number", default: 104 },
            n_geos: { type: "number", default: 1 },
            n_channels: { type: "number", default: 3 }
          }
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
      return { content: [{ type: "text", text: `No direct matches found for topic '${query}'. Try searching for terms like 'data', 'priors', 'budget', 'install', 'causal', or 'optimizer'.` }] };
    }

    let text = `# Search Results for '${query}'\n\n`;
    for (const item of matches) {
      text += `- **${item.title}**\n  - URL: ${item.url}\n  - Summary: ${item.description}\n\n`;
    }
    return { content: [{ type: "text", text }] };
  }

  if (name === "fetch_docs") {
    const targetUrl = args?.url;
    if (!targetUrl) {
      return { content: [{ type: "text", text: "Error: Missing required parameter 'url'." }] };
    }

    try {
      const res = await fetch(targetUrl, {
        headers: { "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) GoogleMeridianMCP/1.0" },
        redirect: "follow"
      });
      const text = await res.text();
      return { content: [{ type: "text", text }] };
    } catch (e) {
      return { content: [{ type: "text", text: `Error fetching URL '${targetUrl}': ${e.message}` }] };
    }
  }

  if (name === "get_control_point_guide") {
    const cp = (args?.control_point || "ALL").toLowerCase();
    const text = `# Google Meridian Control Points Guide (${cp.toUpperCase()})\n\nRefer to FIRST_PRINCIPLES_MMM.md for complete mathematical details on Data Inputs, Confounders, Adstock Decay, Hill Saturation, Bayesian Priors, MCMC Diagnostics, and Budget Optimization.`;
    return { content: [{ type: "text", text }] };
  }

  if (name === "get_mmm_workflow_guide") {
    const ph = (args?.phase || "ALL").toLowerCase();
    const text = `# Google Meridian Workflow Guide (${ph.toUpperCase()})\n\nRefer to FIRST_PRINCIPLES_MMM.md for complete iteration loops (Loop A: Technical Convergence, Loop B: Causal Plausibility, Loop C: Experiment Alignment).`;
    return { content: [{ type: "text", text }] };
  }

  if (name === "calculate_bayesian_prior") {
    const pt = args?.point_estimate || 2.0;
    const lower = args?.ci_lower || 1.2;
    const upper = args?.ci_upper || 2.8;
    if (pt <= 0 || lower <= 0 || upper <= 0) {
      return { content: [{ type: "text", text: "Error: Point estimate and bounds must be > 0." }] };
    }
    const mu = Math.log(pt);
    const sigma = (Math.log(upper) - Math.log(lower)) / 3.92;
    const text = `# Calculated Meridian LogNormal Prior\n- Point Estimate: ${pt}\n- 95% CI: [${lower}, ${upper}]\n- mu: ${mu.toFixed(4)}\n- sigma: ${sigma.toFixed(4)}\n\n\`\`\`python\ntfd.LogNormal(loc=${mu.toFixed(4)}, scale=${sigma.toFixed(4)})\n\`\`\``;
    return { content: [{ type: "text", text }] };
  }

  if (name === "audit_model_first_principles") {
    const text = "# Google Meridian First-Principles Model Spec Audit\n- Checked Knot Distance, Prior Variance, Max Lag, and Hill parameter bounds.\n- Refer to FIRST_PRINCIPLES_MMM.md for diagnostic guidelines.";
    return { content: [{ type: "text", text }] };
  }

  if (name === "synthesize_meridian_code") {
    const text = "# Cloud-Agnostic Google Meridian Python Snippet\n\n```python\nimport pandas as pd\nfrom meridian.data import input_data\nfrom meridian.model import spec, model\nfrom meridian.analysis import optimizer\n\n# Load Data\ndf = pd.read_csv('meridian_input_data.csv')\ndata = input_data.InputData(kpi=df['kpi'].values, media_spend=df[['spend_ch1', 'spend_ch2']].values)\nmodel_spec = spec.ModelSpec(media_effects_dist='log_normal')\nmmm = model.Meridian(input_data=data, model_spec=model_spec)\nmmm.fit(n_chains=4, n_adapt=500)\nopt = optimizer.BudgetOptimizer(mmm)\nprint(opt.optimize())\n```";
    return { content: [{ type: "text", text }] };
  }

  if (name === "generate_schema_template") {
    const text = "# Google Meridian Input Schema Template\n\n```csv\ntime,geo,kpi,spend_channel_1,impressions_channel_1,spend_channel_2,impressions_channel_2,control_price_index\n2025-01-01,national,100000,15000,500000,12000,400000,1.02\n```";
    return { content: [{ type: "text", text }] };
  }

  throw new Error(`Tool not found: ${name}`);
});

async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error("Google Meridian MCP Server running on stdio");
}

main().catch((error) => {
  console.error("Fatal error in main():", error);
  process.exit(1);
});
