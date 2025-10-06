# Integrating Claude Agent SDK with Your Existing MCP Servers

## Overview

Your **ai-content-engine** project already has a sophisticated MCP architecture with OAuth2-secured Spring Boot MCP servers. This guide shows how to integrate the **Claude Agent SDK** (Python) with your existing Java-based MCP infrastructure.

## Your Current Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   Content Engine (Java/Spring)              │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Spring AI MCP Client                                │   │
│  │  - OAuth2 token provider (client_credentials)        │   │
│  │  - HttpClientStreamableHttpTransport                 │   │
│  │  - Authenticated requests to MCP servers             │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                        ↓ HTTP + JWT Bearer Token
        ┌───────────────┴───────────────┐
        ↓                               ↓
┌────────────────────┐         ┌────────────────────┐
│ Finance MCP Server │         │Discovery MCP Server│
│ (Spring Boot)      │         │ (Spring Boot)      │
│                    │         │                    │
│ Port: 8081         │         │ Port: 8084         │
│ Endpoint: /mcp     │         │ Endpoint: /mcp     │
│                    │         │                    │
│ Tools:             │         │ Tools:             │
│ - FRED API         │         │ - RSS feeds        │
│ - FMP (earnings)   │         │ - ArXiv search     │
│ - Yahoo Finance    │         │ - PubMed search    │
│ - Treasury yields  │         │ - Wikipedia        │
│ - Real estate data │         │ - HTML fetch       │
└────────────────────┘         └────────────────────┘
        ↑                               ↑
        └───────────────┬───────────────┘
                        │ Protected by OAuth2 JWT
                        │ Issued by:
            ┌───────────────────────────┐
            │ Authorization Server      │
            │ (Spring Authorization)    │
            │ Port: 9090                │
            └───────────────────────────┘
```

## Key Components in Your System

### 1. Authorization Server (Port 9090)
- **Type**: Spring Authorization Server
- **Purpose**: Issues OAuth2 JWT tokens using client_credentials flow
- **Location**: `authorisation-server/`

### 2. MCP Servers (Spring Boot)
- **Finance MCP** (Port 8081): Financial data tools (220+ tools total across all servers)
- **Discovery MCP** (Port 8084): News, RSS, academic search
- **STEM MCP** (mentioned in docs): NASA, environment, medical data

**Security**: All MCP servers require JWT Bearer tokens from the Authorization Server

### 3. Content Engine MCP Client (Java)
- Uses `OAuth2McpTokenProvider` to get tokens via client_credentials
- `HttpClientStreamableHttpTransport` adds `Authorization: Bearer <token>` header
- Configured in `McpClientAuthConfig.java`

## Integration Strategy: Claude Agent SDK → Your MCP Servers

Since your MCP servers are **remote HTTP services** (not in-process Python), you'll use the Claude Agent SDK's ability to connect to **external MCP servers via HTTP**.

### Architecture with Claude Agent SDK

```
┌────────────────────────────────────────────┐
│  Your New Python Agent                     │
│  (Claude Agent SDK)                        │
│                                            │
│  ┌──────────────────────────────────────┐  │
│  │  ClaudeSDKClient                     │  │
│  │  + MCP HTTP Transport                │  │
│  │  + OAuth2 Token Provider (Python)    │  │
│  └──────────────────────────────────────┘  │
└────────────────────────────────────────────┘
                    ↓ HTTP + JWT Bearer Token
        ┌───────────┴───────────────┐
        ↓                           ↓
  Finance MCP (8081)        Discovery MCP (8084)
  (Your existing servers - no changes needed!)
```

## Implementation Steps

### Step 1: Connect to Remote MCP Servers with OAuth2 Auth

The Claude Agent SDK supports remote HTTP/SSE MCP servers with custom headers for authentication!

```python
# agent_with_remote_mcp.py
import asyncio
import os
from dotenv import load_dotenv
from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions
from oauth_token_provider import OAuth2TokenProvider

load_dotenv()

async def main():
    # Setup OAuth2 token provider
    token_provider = OAuth2TokenProvider(
        token_url=os.getenv("AUTH_SERVER_TOKEN_URL", "http://localhost:9090/oauth2/token"),
        client_id=os.getenv("MCP_CLIENT_ID"),
        client_secret=os.getenv("MCP_CLIENT_SECRET")
    )

    # Get a fresh token
    token = token_provider.get_token()

    # Configure remote MCP servers with authentication
    options = ClaudeAgentOptions(
        mcp_servers={
            "finance-mcp": {
                "type": "http",  # or "sse" if your server uses SSE
                "url": os.getenv("FINANCE_MCP_URL", "http://localhost:8081/mcp"),
                "headers": {
                    "Authorization": f"Bearer {token}"
                }
            },
            "discovery-mcp": {
                "type": "http",  # or "sse"
                "url": os.getenv("DISCOVERY_MCP_URL", "http://localhost:8084/mcp"),
                "headers": {
                    "Authorization": f"Bearer {token}"
                }
            }
        },
        # Allow tools from both servers
        allowed_tools=[
            "mcp__finance-mcp__*",  # All finance tools
            "mcp__discovery-mcp__*"  # All discovery tools
        ]
    )

    # Create client and query
    async with ClaudeSDKClient(options=options) as client:
        await client.query(
            "Get the latest earnings for AAPL and search for recent Apple news"
        )

        async for message in client.receive_response():
            print(message)


if __name__ == "__main__":
    asyncio.run(main())
```

### Step 2: Create OAuth2 Token Provider

Create a Python module to get OAuth2 tokens from your Authorization Server:

```python
# oauth_token_provider.py
import requests
from typing import Optional
from datetime import datetime, timedelta

class OAuth2TokenProvider:
    """
    Obtains OAuth2 tokens from your Spring Authorization Server
    using client_credentials flow.
    """

    def __init__(self, token_url: str, client_id: str, client_secret: str):
        self.token_url = token_url
        self.client_id = client_id
        self.client_secret = client_secret
        self._token: Optional[str] = None
        self._expires_at: Optional[datetime] = None

    def get_token(self) -> str:
        """Get a valid access token, refreshing if needed."""
        if self._token and self._expires_at and datetime.now() < self._expires_at:
            return self._token

        # Request new token
        response = requests.post(
            self.token_url,
            data={
                "grant_type": "client_credentials",
                "scope": "mcp.read"  # Adjust scope as needed
            },
            auth=(self.client_id, self.client_secret),
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        response.raise_for_status()

        token_data = response.json()
        self._token = token_data["access_token"]
        expires_in = token_data.get("expires_in", 3600)
        self._expires_at = datetime.now() + timedelta(seconds=expires_in - 60)  # 60s buffer

        return self._token
```

### Step 2: Create HTTP MCP Transport with Auth

Unfortunately, the Claude Agent SDK currently focuses on **in-process MCP servers**. For **remote HTTP MCP servers**, you'll need to use the lower-level MCP client libraries.

**Alternative Approach**: Use the **MCP Python SDK** directly with Claude:

```python
# mcp_remote_client.py
import asyncio
from anthropic import Anthropic
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
import httpx
from oauth_token_provider import OAuth2TokenProvider

class AuthenticatedMcpHttpClient:
    """
    MCP client that connects to your remote HTTP MCP servers
    with OAuth2 authentication.
    """

    def __init__(self, server_url: str, token_provider: OAuth2TokenProvider):
        self.server_url = server_url
        self.token_provider = token_provider

    async def get_tools(self):
        """Fetch available tools from the MCP server."""
        token = self.token_provider.get_token()

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.server_url}/mcp/tools",  # Adjust endpoint as needed
                headers={"Authorization": f"Bearer {token}"}
            )
            response.raise_for_status()
            return response.json()

    async def call_tool(self, tool_name: str, arguments: dict):
        """Call a tool on the remote MCP server."""
        token = self.token_provider.get_token()

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.server_url}/mcp/call",  # Adjust endpoint as needed
                json={"tool": tool_name, "arguments": arguments},
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json"
                }
            )
            response.raise_for_status()
            return response.json()
```

### Step 3: Integrate with Anthropic SDK (Direct Approach)

Since Claude Agent SDK wraps Claude Code (which may not support external HTTP MCP servers easily), use the **Anthropic SDK directly** with manual tool handling:

```python
# agent_with_remote_mcp.py
import asyncio
import os
from dotenv import load_dotenv
from anthropic import Anthropic
from oauth_token_provider import OAuth2TokenProvider
from mcp_remote_client import AuthenticatedMcpHttpClient

load_dotenv()

async def main():
    # Setup OAuth2 token provider
    token_provider = OAuth2TokenProvider(
        token_url=os.getenv("AUTH_SERVER_TOKEN_URL", "http://localhost:9090/oauth2/token"),
        client_id=os.getenv("MCP_CLIENT_ID"),
        client_secret=os.getenv("MCP_CLIENT_SECRET")
    )

    # Connect to your MCP servers
    finance_mcp = AuthenticatedMcpHttpClient(
        server_url=os.getenv("FINANCE_MCP_URL", "http://localhost:8081"),
        token_provider=token_provider
    )

    discovery_mcp = AuthenticatedMcpHttpClient(
        server_url=os.getenv("DISCOVERY_MCP_URL", "http://localhost:8084"),
        token_provider=token_provider
    )

    # Get tools from MCP servers
    finance_tools = await finance_mcp.get_tools()
    discovery_tools = await discovery_mcp.get_tools()

    # Convert MCP tools to Anthropic tool format
    all_tools = convert_mcp_tools_to_anthropic(finance_tools + discovery_tools)

    # Initialize Claude
    client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    # Agent loop
    messages = [{
        "role": "user",
        "content": "Get the latest earnings data for AAPL and search for recent news about Apple"
    }]

    while True:
        response = client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=4096,
            tools=all_tools,
            messages=messages
        )

        if response.stop_reason == "tool_use":
            # Handle tool calls by routing to appropriate MCP server
            for content_block in response.content:
                if content_block.type == "tool_use":
                    tool_name = content_block.name
                    tool_input = content_block.input

                    # Route to correct MCP server
                    if tool_name.startswith("finance_"):
                        result = await finance_mcp.call_tool(tool_name, tool_input)
                    elif tool_name.startswith("discovery_"):
                        result = await discovery_mcp.call_tool(tool_name, tool_input)

                    # Add tool result to messages
                    messages.append({"role": "assistant", "content": response.content})
                    messages.append({
                        "role": "user",
                        "content": [{
                            "type": "tool_result",
                            "tool_use_id": content_block.id,
                            "content": str(result)
                        }]
                    })
            continue

        elif response.stop_reason == "end_turn":
            for content_block in response.content:
                if hasattr(content_block, "text"):
                    print(content_block.text)
            break


def convert_mcp_tools_to_anthropic(mcp_tools):
    """Convert MCP tool schema to Anthropic tool format."""
    anthropic_tools = []
    for tool in mcp_tools:
        anthropic_tools.append({
            "type": "custom",
            "name": tool["name"],
            "description": tool["description"],
            "input_schema": tool["inputSchema"]
        })
    return anthropic_tools


if __name__ == "__main__":
    asyncio.run(main())
```

## Configuration

Create `.env` file in your Python agent project:

```bash
# OAuth2 Configuration (same as your Java content-engine)
AUTH_SERVER_TOKEN_URL=http://localhost:9090/oauth2/token
MCP_CLIENT_ID=your-client-id
MCP_CLIENT_SECRET=your-client-secret

# MCP Server URLs
FINANCE_MCP_URL=http://localhost:8081
DISCOVERY_MCP_URL=http://localhost:8084
STEM_MCP_URL=http://localhost:8085  # If you have STEM server

# Anthropic API
ANTHROPIC_API_KEY=your-anthropic-api-key
```

## Reusing Your Authorization Server

Your Python agent will use the **same OAuth2 flow** as your Java content-engine:

1. **Client Registration**: Register a new OAuth2 client in your Spring Authorization Server for the Python agent
2. **Grant Type**: `client_credentials`
3. **Scope**: Same scopes your Java client uses (e.g., `mcp.read`)
4. **Token Endpoint**: `http://localhost:9090/oauth2/token` (or production URL)

**Register client in Authorization Server:**

```java
// In your Spring Authorization Server configuration
RegisteredClient pythonAgent = RegisteredClient.withId(UUID.randomUUID().toString())
    .clientId("python-agent")
    .clientSecret(passwordEncoder.encode("python-agent-secret"))
    .clientAuthenticationMethod(ClientAuthenticationMethod.CLIENT_SECRET_BASIC)
    .authorizationGrantType(AuthorizationGrantType.CLIENT_CREDENTIALS)
    .scope("mcp.read")
    .build();
```

## Benefits of This Approach

1. **No changes to existing MCP servers** - They continue serving your Java content-engine
2. **Reuse existing OAuth2 infrastructure** - Same Authorization Server
3. **Consistent security model** - All clients use JWT tokens
4. **Language flexibility** - Python agents can access your Java MCP tools
5. **Gradual migration** - Run Java and Python agents side-by-side

## Alternative: Simplified Testing Approach

For local development/testing, you could temporarily bypass OAuth2:

```python
# Simple HTTP client for local testing (NO AUTH - dev only!)
class SimpleMcpClient:
    def __init__(self, server_url: str):
        self.server_url = server_url

    async def call_tool(self, tool_name: str, arguments: dict):
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.server_url}/mcp/call",
                json={"tool": tool_name, "arguments": arguments}
            )
            return response.json()
```

**Note**: Only for local dev. Production must use OAuth2.

## Production Considerations

1. **Token Caching**: The `OAuth2TokenProvider` caches tokens to avoid unnecessary auth server calls
2. **Error Handling**: Add retry logic for token refresh failures
3. **Connection Pooling**: Reuse HTTP connections to MCP servers
4. **Monitoring**: Log MCP tool calls for debugging
5. **Rate Limiting**: Your MCP servers may have rate limits
6. **Network**: In production, ensure Python agent can reach MCP servers (firewall rules, VPCs, etc.)

## MCP Protocol Compatibility

Your Spring Boot MCP servers implement the **MCP SSE (Server-Sent Events)** protocol. The Python MCP client needs to support the same protocol version. Check:

- Spring AI MCP version in your Java projects
- MCP Python SDK version
- Ensure protocol compatibility (both should use MCP 1.x specification)

## Example: Multi-Domain Content Generation

```python
async def generate_finance_article():
    """Example: Generate article using finance and discovery MCP tools."""

    # Your agent can now use tools from both MCP servers
    messages = [{
        "role": "user",
        "content": (
            "Research Apple's latest earnings using the finance tools, "
            "then search for related news articles using discovery tools, "
            "and write a comprehensive analysis article."
        )
    }]

    # Claude will:
    # 1. Call finance_mcp tools: get_earnings_calendar, get_stock_price
    # 2. Call discovery_mcp tools: search_news, fetch_article_content
    # 3. Synthesize everything into an article

    # (Use the agent loop from Step 3 above)
```

## Resources

- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)
- [Anthropic Tool Calling](https://docs.anthropic.com/en/docs/build-with-claude/tool-use)
- [Spring Authorization Server](https://spring.io/projects/spring-authorization-server)
- Your existing docs:
  - `ai-content-engine/content-engine/README.md`
  - `ai-content-engine/finance-mcp-server/README.md`
  - `ai-content-engine/discovery-mcp-server/README.md`

## Summary

**The Claude Agent SDK DOES support remote HTTP MCP servers!** Simply configure them in `ClaudeAgentOptions`:

1. ✅ **Use Claude Agent SDK** with remote HTTP/SSE transport
2. ✅ **Add OAuth2 headers** directly in the MCP server configuration
3. ✅ **Reuse your Authorization Server** - register Python agent as OAuth2 client
4. ✅ **No changes to existing MCP servers** - they already support HTTP/SSE
5. ✅ **Automatic tool handling** - Claude Agent SDK manages the agentic loop

This is much simpler than manual tool handling and perfectly compatible with your existing Spring Boot MCP infrastructure!

## Token Refresh Consideration

**Note**: The above examples get a token once at startup. For long-running agents, you'll need to refresh tokens periodically. Consider:

1. Creating a background task to refresh tokens before expiry
2. Or: Implement a custom `McpServerConfig` that dynamically updates headers
3. Or: Use shorter-lived sessions and recreate the `ClaudeSDKClient` periodically

Check Claude Agent SDK docs for advanced transport customization options.
