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
