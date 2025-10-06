# Claude Agent SDK Architecture

## Overview

The **Claude Agent SDK** is a Python library that provides programmatic access to **Claude Code's** functionality. It allows you to build AI agents that can use tools, maintain conversation context, and autonomously complete complex tasks.

## Relationship: Claude Agent SDK ↔ Claude Code

**Important:** Claude Agent SDK is NOT independent of Claude Code - it's a programmatic wrapper that embeds Claude Code within your Python application.

```
┌─────────────────────────────────────┐
│   Your Python Application           │
│                                     │
│   ┌─────────────────────────────┐   │
│   │  Claude Agent SDK           │   │
│   │  (Python Library)           │   │
│   └─────────────────────────────┘   │
│              ↓ embeds/wraps         │
│   ┌─────────────────────────────┐   │
│   │  Claude Code Engine         │   │
│   │  (Built-in Tools)           │   │
│   │  - Bash, Read, Write, Edit  │   │
│   │  - WebSearch, Grep, Glob    │   │
│   │  - Task, TodoWrite, etc.    │   │
│   └─────────────────────────────┘   │
│              ↓                      │
│   ┌─────────────────────────────┐   │
│   │  Anthropic API              │   │
│   │  (Claude Models)            │   │
│   └─────────────────────────────┘   │
└─────────────────────────────────────┘
```

**Key Points:**
- **Claude Agent SDK = Programmatic API for Claude Code**
- Claude Code runs embedded within your Python process when you use the SDK
- Built-in tools (Bash, Read, Write, WebSearch, etc.) are **Claude Code's tools**, not SDK-specific
- You get ALL of Claude Code's capabilities programmatically
- The SDK provides the same power as running `claude-code` CLI, but with Python control

**Verified in Practice:**
When you create a `ClaudeSDKClient`, the `SystemMessage` shows all Claude Code tools are available:
```python
'tools': ['Task', 'Bash', 'Glob', 'Grep', 'Read', 'Write', 'Edit',
          'WebSearch', 'TodoWrite', 'NotebookEdit', ...]
```
These aren't SDK tools - they're Claude Code's tools exposed programmatically!

## Core Components

### 1. Two Interaction Methods

#### `query()` - One-off Tasks
```python
from claude_agent_sdk import query

async for message in query(prompt="What files are in this directory?"):
    print(message)
```
- Creates a new session for each call
- Best for independent, single tasks
- Simple and straightforward

#### `ClaudeSDKClient` - Continuous Conversations
```python
from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions

async with ClaudeSDKClient(options=options) as client:
    await client.query("Hello")
    async for response in client.receive_response():
        print(response)

    await client.query("What did I just say?")  # Has context!
    async for response in client.receive_response():
        print(response)
```
- Maintains conversation context across multiple turns
- Supports advanced features (interrupts, hooks, streaming)
- Best for interactive applications

### 2. Message Flow

```
User Query
    ↓
┌───────────────────────────────────────┐
│ SystemMessage (init)                  │
│ - Session ID, model, tools, etc.      │
└───────────────────────────────────────┘
    ↓
┌───────────────────────────────────────┐
│ AssistantMessage (text)               │
│ - Claude acknowledges task            │
└───────────────────────────────────────┘
    ↓
┌───────────────────────────────────────┐
│ AssistantMessage (tool_use)           │
│ - Claude decides to use a tool        │
└───────────────────────────────────────┘
    ↓
┌───────────────────────────────────────┐
│ UserMessage (tool_result)             │
│ - Tool executes and returns result    │
└───────────────────────────────────────┘
    ↓
┌───────────────────────────────────────┐
│ AssistantMessage (text)               │
│ - Claude synthesizes final answer     │
└───────────────────────────────────────┘
    ↓
┌───────────────────────────────────────┐
│ ResultMessage (summary)               │
│ - Cost, duration, tokens, final result│
└───────────────────────────────────────┘
```

## Built-in Tools (From Claude Code)

When you see this in `SystemMessage`:
```python
'tools': ['Task', 'Bash', 'Glob', 'Grep', 'ExitPlanMode', 'Read', 'Edit',
          'Write', 'NotebookEdit', 'WebFetch', 'TodoWrite', 'WebSearch',
          'BashOutput', 'KillShell', 'SlashCommand', 'mcp__search__web_search']
```

These tools are provided by **Claude Code**:
- **Bash** - Execute shell commands
- **Read** - Read files
- **Write** - Create/overwrite files
- **Edit** - Modify existing files
- **Grep** - Search file contents
- **Glob** - Find files by pattern
- **WebSearch** - Search the internet
- **WebFetch** - Fetch web pages
- **TodoWrite** - Manage task lists
- **Task** - Launch sub-agents
- **Notebook** - Work with Jupyter notebooks

Your custom tools (prefixed with `mcp__`) are added via MCP servers.

## Adding Custom Tools via MCP

### Why MCP is Required for Custom Tools

**Important:** Claude Agent SDK **only** supports custom tools through MCP servers. You cannot define tools directly like you can with the Anthropic SDK.

**Why?** Claude Agent SDK embeds Claude Code, which uses MCP as its tool protocol. All tools - both built-in (Bash, Read, etc.) and custom - must be MCP-compatible.

**Two Options for Custom Tools:**

1. **In-process MCP server** (what we used in `agent.py`):
   - Created with `@tool` decorator + `create_sdk_mcp_server()`
   - Runs within your Python process
   - Simple for local logic
   - Similar to Spring AI's `@Bean ToolCallbackProvider`

2. **Remote MCP server** (like your Spring Boot servers):
   - Already running on HTTP/SSE
   - Connected via URL + headers
   - Shared across multiple clients
   - Production-grade with OAuth2 security

**This is different from using Anthropic SDK directly**, where you can pass tool schemas without MCP:
```python
# Anthropic SDK - Direct tool definition (NO MCP)
client.messages.create(
    tools=[{"type": "custom", "name": "search", ...}]  # Direct schema
)

# Claude Agent SDK - MUST use MCP
options = ClaudeAgentOptions(
    mcp_servers={"search": create_sdk_mcp_server(...)}  # MCP required
)
```

### Step 1: Define a Tool

```python
from claude_agent_sdk import tool

@tool("calculator", "Performs math calculations", {"expression": str})
async def calculator(args):
    """Execute a calculation."""
    result = eval(args["expression"], {"__builtins__": {}})
    return {
        "content": [{
            "type": "text",
            "text": f"Result: {result}"
        }]
    }
```

### Step 2: Create an MCP Server

```python
from claude_agent_sdk import create_sdk_mcp_server

my_server = create_sdk_mcp_server(
    name="math",
    version="1.0.0",
    tools=[calculator]
)
```

### Step 3: Register with ClaudeAgentOptions

```python
from claude_agent_sdk import ClaudeAgentOptions

options = ClaudeAgentOptions(
    mcp_servers={"math": my_server},
    allowed_tools=["mcp__math__calculator"]  # Tool name format: mcp__{server}__{tool}
)
```

### Step 4: Use in Client

```python
async with ClaudeSDKClient(options=options) as client:
    await client.query("What's 123 * 456?")
    async for message in client.receive_response():
        print(message)
```

## Limiting Tools

### Allow Only Specific Tools

```python
options = ClaudeAgentOptions(
    allowed_tools=["Read", "Write", "mcp__search__web_search"]
)
```

### Disallow Specific Tools

```python
options = ClaudeAgentOptions(
    disallowed_tools=["Bash", "WebSearch"]
)
```

### Multiple MCP Servers

```python
search_server = create_sdk_mcp_server(name="search", version="1.0.0", tools=[web_search])
math_server = create_sdk_mcp_server(name="math", version="1.0.0", tools=[calculator])

options = ClaudeAgentOptions(
    mcp_servers={
        "search": search_server,
        "math": math_server
    },
    allowed_tools=[
        "mcp__search__web_search",
        "mcp__math__calculator",
        "Read",  # Also allow built-in Read tool
        "Write"  # Also allow built-in Write tool
    ]
)
```

## Multi-Agent Workflows

### Using Sub-Agents with the Task Tool

The built-in **Task** tool allows Claude to spawn specialized sub-agents:

```python
# The Task tool is available by default
options = ClaudeAgentOptions(
    allowed_tools=["Task", "Read", "Write", "Bash"]
)

async with ClaudeSDKClient(options=options) as client:
    await client.query(
        "First, research the best Python web frameworks by reading docs. "
        "Then, create a new Flask project with proper structure."
    )
    # Claude can use Task tool to spawn sub-agents for different steps
    async for message in client.receive_response():
        print(message)
```

### Custom Agent Definitions (Advanced)

You can define custom agents with specific capabilities:

```python
from claude_agent_sdk import AgentDefinition

options = ClaudeAgentOptions(
    agents={
        "code_reviewer": AgentDefinition(
            description="Reviews code for quality and security",
            system_prompt="You are a senior software engineer focused on code quality",
            tools=["Read", "Grep", "Glob"]
        ),
        "test_writer": AgentDefinition(
            description="Writes unit tests",
            system_prompt="You are an expert in writing comprehensive unit tests",
            tools=["Read", "Write", "Bash"]
        )
    }
)
```

### Orchestrating Multiple Agents

```python
async with ClaudeSDKClient(options=options) as client:
    # Main agent coordinates sub-agents
    await client.query(
        "Review the code in src/ for security issues, "
        "then write tests for any vulnerable functions found."
    )

    # Claude orchestrates:
    # 1. Spawns code_reviewer agent to analyze src/
    # 2. Spawns test_writer agent to create tests
    # 3. Synthesizes final report

    async for message in client.receive_response():
        print(message)
```

## ClaudeAgentOptions - Full Configuration

```python
options = ClaudeAgentOptions(
    # Model selection
    model="claude-sonnet-4-5-20250929",

    # System prompt customization
    system_prompt="You are a helpful coding assistant specialized in Python",

    # MCP servers (custom tools)
    mcp_servers={"search": search_server, "math": math_server},

    # Tool restrictions
    allowed_tools=["Read", "Write", "mcp__search__web_search"],
    disallowed_tools=["Bash", "WebSearch"],

    # Permission modes
    permission_mode="default",  # or "strict", "permissive"

    # Custom agents
    agents={
        "reviewer": AgentDefinition(...)
    },

    # Environment variables
    env_vars={"API_KEY": "secret"},

    # Hooks for event interception
    hooks={
        "on_tool_use": my_tool_use_handler,
        "on_message": my_message_handler
    },

    # Session configuration
    session_id="custom-session-id",
    cwd="/path/to/working/directory"
)
```

## Permission Modes

- **`default`** - Balanced: prompts for dangerous operations
- **`strict`** - High security: requires approval for most tool uses
- **`permissive`** - Low friction: allows most operations without prompting

```python
options = ClaudeAgentOptions(
    permission_mode="strict",  # More security
    allowed_tools=["Read"]     # Further restrict to read-only
)
```

## Cost and Token Management

Every `ResultMessage` includes usage information:

```python
{
    'total_cost_usd': 0.0131,
    'duration_ms': 7440,
    'num_turns': 4,
    'usage': {
        'input_tokens': 9,
        'cache_read_input_tokens': 29890,  # Prompt caching saves money!
        'output_tokens': 258
    }
}
```

**Prompt Caching:**
- Tool schemas are automatically cached
- Repeated calls with same tools cost less
- Notice `cache_read_input_tokens` >> `input_tokens`

## Best Practices

1. **Use `allowed_tools`** to restrict agent capabilities for security
2. **Leverage prompt caching** by reusing MCP servers across sessions
3. **Use sub-agents** (Task tool) for complex, multi-step workflows
4. **Monitor costs** via `ResultMessage.total_cost_usd`
5. **Implement hooks** for logging, monitoring, and debugging
6. **Start with `permission_mode="strict"`** in production

## Example: Production Agent

```python
import asyncio
from claude_agent_sdk import (
    tool, create_sdk_mcp_server, ClaudeSDKClient, ClaudeAgentOptions
)
from dotenv import load_dotenv

load_dotenv()

@tool("database_query", "Query the database", {"sql": str})
async def database_query(args):
    # Production: use actual database
    result = await db.execute(args["sql"])
    return {"content": [{"type": "text", "text": str(result)}]}

async def main():
    db_server = create_sdk_mcp_server(
        name="database",
        version="1.0.0",
        tools=[database_query]
    )

    options = ClaudeAgentOptions(
        model="claude-sonnet-4-5-20250929",
        mcp_servers={"database": db_server},
        allowed_tools=["mcp__database__database_query", "Read"],
        permission_mode="strict",
        system_prompt="You are a data analyst. Only run SELECT queries."
    )

    async with ClaudeSDKClient(options=options) as client:
        await client.query("Show me sales data for Q4 2024")
        async for message in client.receive_response():
            if type(message).__name__ == "ResultMessage":
                print(f"Cost: ${message.total_cost_usd:.4f}")
                print(f"Result: {message.result}")

if __name__ == "__main__":
    asyncio.run(main())
```

## Resources

- [Claude Agent SDK Documentation](https://docs.claude.com/en/api/agent-sdk/python)
- [Model Context Protocol (MCP)](https://modelcontextprotocol.io/)
- [Claude Code Documentation](https://docs.claude.com/claude-code)