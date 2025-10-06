# Claude Agent SDK Example

A simple Python agent using the **Claude Agent SDK** with a custom web search tool (stubbed results).

## Prerequisites

- Python 3.13
- uv (Python package manager)
- Anthropic API key

## Setup

1. **Create `.env` file** with your API key:
   ```
   ANTHROPIC_API_KEY=your_api_key_here
   ```

2. **Install dependencies**:
   ```bash
   uv sync
   ```
   This installs all dependencies into `.venv` (similar to `mvn install` in Maven).

## Running the Agents

### Basic Example: Stubbed Search Tool

**From terminal:**
```bash
uv run python agent.py
```

**From IntelliJ IDEA:**
- Right-click `agent.py` → **Debug** (Debug mode shows output better than Run mode in IntelliJ)
- Or use the built-in Terminal tab: `uv run python agent.py`

### Real Use Case: Weekly LinkedIn Article Generator

Generate a LinkedIn post consolidating the week's content from [macrospire.com](https://macrospire.com):

```bash
# 1. Configure production credentials in .env
AUTH_SERVER_TOKEN_URL=https://auth.macrospire.com/oauth2/token
MCP_CLIENT_ID=<your-client-id>
MCP_CLIENT_SECRET=<your-client-secret>
FINANCE_MCP_URL=https://finance.macrospire.com/mcp
DISCOVERY_MCP_URL=https://discovery.macrospire.com/mcp
STEM_MCP_URL=https://stem.macrospire.com/mcp
ANTHROPIC_API_KEY=<your-api-key>

# 2. Run the agent
uv run python weekly_linkedin_agent.py
```

**What it does:**
- Connects to production MCP servers (finance, discovery, stem)
- Fetches last week's articles from macrospire.com
- Analyzes key insights across domains
- Generates an engaging LinkedIn post
- Saves to `linkedin_article_YYYYMMDD.md`

**See**: [WEEKLY_LINKEDIN_USE_CASE.md](WEEKLY_LINKEDIN_USE_CASE.md) for detailed comparison with Spring AI implementation.

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

## How it Works

The agent uses the **Claude Agent SDK** which provides:
- Automatic agentic loops (no manual tool handling needed)
- MCP (Model Context Protocol) for tool integration
- Built-in tools (Task, Bash, Read, Write, etc.)
- Structured message flow

**agent.py** contains:
1. **`web_search` tool** - Defined using `@tool` decorator, returns stubbed search results
2. **MCP server** - Created with `create_sdk_mcp_server()` to register the tool
3. **ClaudeSDKClient** - Handles the conversation and tool execution automatically

The agent:
- Receives query: "Search for 'claude code'"
- Automatically calls the `web_search` tool
- Formats and presents the 3 stubbed results

## Key Concepts

- **`@tool` decorator**: Define custom tools with name, description, and schema
- **MCP Server**: Register tools using Model Context Protocol
- **ClaudeSDKClient**: Async client that manages conversations and tool execution
- **Async/await**: Agent SDK uses asyncio for non-blocking operations

## Next Steps

To extend this agent:
- Replace stubbed results with real search API (Google, Bing, DuckDuckGo, Tavily, etc.)
- Add more custom tools (file operations, API calls, calculations, etc.)
- Implement conversation history for multi-turn interactions
- Add error handling and retries for production use

## Resources

- [Claude Agent SDK Documentation](https://docs.claude.com/en/api/agent-sdk/python)
- [MCP Protocol](https://modelcontextprotocol.io/)