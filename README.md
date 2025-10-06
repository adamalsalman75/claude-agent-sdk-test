# Weekly LinkedIn Article Generator

**Autonomous AI agent** that generates LinkedIn posts consolidating weekly content from [macrospire.com](https://macrospire.com), using **Claude Agent SDK** with production MCP servers.

## What It Does

1. 🔐 Authenticates with your Spring Authorization Server (OAuth2)
2. 🌐 Fetches last week's articles from macrospire.com
3. 📊 Cross-checks with **live market data** from Finance MCP tools:
   - Real-time stock prices (NKE, TSLA, etc.)
   - Earnings reports & analyst estimates
   - Treasury yields & economic indicators
   - Analyst upgrades/downgrades
4. ✍️ Generates engaging LinkedIn article with fresh insights
5. 💾 Saves to `linkedin_article_YYYYMMDD.md`

## Prerequisites

- Python 3.13
- uv (Python package manager)
- Anthropic API key
- Access to your production MCP servers

## Setup

### 1. Install Dependencies

```bash
uv sync
```

This installs all dependencies into `.venv` (similar to `mvn install` in Maven).

### 2. Configure Environment Variables

Create a `.env` file with your credentials:

```bash
# Anthropic API
ANTHROPIC_API_KEY=your-anthropic-key

# OAuth2 credentials (from your Spring Authorization Server)
AUTH_SERVER_TOKEN_URL=https://auth.macrospire.com/oauth2/token
MCP_CLIENT_ID=content-engine-client
MCP_CLIENT_SECRET=your-secret-here

# Production MCP server URLs
FINANCE_MCP_URL=https://finance.macrospire.com/mcp
```

**Note:** The OAuth2 credentials should match those registered in your Spring Authorization Server with scopes: `mcp:read`, `mcp:write`, `mcp:tools`

## Running the Agent

### From Terminal:
```bash
uv run python weekly_linkedin_agent.py
```

### From IntelliJ IDEA:
- Right-click `weekly_linkedin_agent.py` → **Debug** (Debug mode shows output better than Run mode)
- Or use the built-in Terminal tab: `uv run python weekly_linkedin_agent.py`

## Expected Output

```
✅ Obtained OAuth2 token from https://auth.macrospire.com/oauth2/token

🤖 Starting Weekly LinkedIn Article Generation
📅 Date Range: 2025-09-29 to 2025-10-06
🔧 Connected to MCP Server:
   - Finance: https://finance.macrospire.com/mcp

[Agent executes...]

📊 GENERATION SUMMARY
✅ Status: success
⏱️  Duration: 82.44s
💰 Cost: $0.1400
🔄 Turns: 30
📝 Input tokens: 19
💾 Cached tokens: 92449  ← Prompt caching saves $$$
📤 Output tokens: 1782

✅ Article saved to: linkedin_article_20251006.md
```

The agent autonomously:
- Fetches macrospire.com articles
- Calls 12+ finance MCP tools (earnings, market data, analyst ratings, etc.)
- Cross-references published articles with live market data
- Generates a compelling LinkedIn post

## Architecture

This project demonstrates **Claude Agent SDK** with:

- **OAuth2 authentication** - Token provider for Spring Authorization Server
- **Remote HTTP MCP servers** - Connects to production finance tools
- **Autonomous agentic workflow** - Claude decides which tools to use
- **Prompt caching** - 90%+ cache hit rate on subsequent runs

See [ARCHITECTURE.md](ARCHITECTURE.md) for technical details.

## Comparison with Spring AI

See [WEEKLY_LINKEDIN_USE_CASE.md](WEEKLY_LINKEDIN_USE_CASE.md) for a detailed comparison:

| Metric | Spring AI (Java) | Claude Agent SDK (Python) |
|--------|------------------|---------------------------|
| **Lines of code** | ~300+ | ~200 |
| **Development time** | 2-3 days | 2 hours |
| **Cost per run** | ~$0.10 | ~$0.05 (first), ~$0.01 (cached) |
| **Workflow** | Manual orchestration | Autonomous |
| **Flexibility** | Code changes required | Prompt changes only |

## IntelliJ IDEA Setup

1. **Install Python plugin**:
   - Settings → Plugins → Search "Python" → Install → Restart

2. **Configure Python interpreter**:
   - Settings → Project → Python Interpreter
   - Gear icon → Add Interpreter → Add Local Interpreter
   - Select "Virtualenv Environment" → Existing
   - Browse to: `<project-root>/.venv/bin/python`

3. **If packages aren't recognized after `uv sync`**:
   - File → Invalidate Caches → Just Restart

## Key Technologies

- **Claude Agent SDK** - Programmatic access to Claude Code's agentic capabilities
- **MCP (Model Context Protocol)** - Standard for connecting AI to tools
- **OAuth2** - Secure authentication with Spring Authorization Server
- **Python 3.13 + uv** - Modern Python with fast dependency management
- **Async/await** - Non-blocking operations for tool execution

## Resources

- [Claude Agent SDK Documentation](https://docs.claude.com/en/api/agent-sdk/python)
- [MCP Protocol](https://modelcontextprotocol.io/)
- [INTEGRATION_WITH_EXISTING_MCP.md](INTEGRATION_WITH_EXISTING_MCP.md) - How to connect to existing Spring Boot MCP servers
- [SPRING_AI_VS_CLAUDE_SDK.md](SPRING_AI_VS_CLAUDE_SDK.md) - Detailed framework comparison