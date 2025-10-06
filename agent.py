"""
Simple agent using the Claude Agent SDK with a stubbed search tool.
"""

import asyncio
from pprint import pprint
from dotenv import load_dotenv
from claude_agent_sdk import tool, create_sdk_mcp_server, ClaudeSDKClient, ClaudeAgentOptions

# Load environment variables from .env file
load_dotenv()


@tool("web_search", "Searches the internet for a given query and returns the top 3 results", {"query": str})
async def web_search(args):
    """Execute a search query and return stubbed results."""
    query = args["query"]

    # Stubbed results
    results = [
        {
            "title": "Claude Code - Official CLI for Claude",
            "url": "https://docs.claude.com/claude-code",
            "snippet": "Claude Code is Anthropic's official command-line interface that brings Claude's AI capabilities directly to your terminal for coding tasks."
        },
        {
            "title": "Getting Started with Claude Code",
            "url": "https://docs.claude.com/claude-code/getting-started",
            "snippet": "Learn how to install and configure Claude Code for your development workflow. Claude Code supports multiple programming languages and integrates with your existing tools."
        },
        {
            "title": "Claude Code GitHub Repository",
            "url": "https://github.com/anthropics/claude-code",
            "snippet": "The official GitHub repository for Claude Code. View source code, report issues, and contribute to the project."
        }
    ]

    # Format results as text
    result_text = f"Search results for '{query}':\n\n"
    for i, result in enumerate(results, 1):
        result_text += f"{i}. {result['title']}\n"
        result_text += f"   URL: {result['url']}\n"
        result_text += f"   {result['snippet']}\n\n"

    return {
        "content": [{
            "type": "text",
            "text": result_text
        }]
    }


def print_message(message):
    """Pretty print messages using pprint."""
    print(f"\n{'=' * 80}")
    print(f"{type(message).__name__}:")
    print('=' * 80)
    # Convert message to dict using vars() for dataclasses or __dict__
    message_dict = vars(message) if hasattr(message, '__dict__') else str(message)
    pprint(message_dict, width=120, compact=False)


async def run_agent():
    """Run the agent to search for Claude Code."""

    # Create MCP server with our search tool
    search_server = create_sdk_mcp_server(
        name="search",
        version="1.0.0",
        tools=[web_search]
    )

    # Configure options to allow the search tool
    options = ClaudeAgentOptions(
        mcp_servers={"search": search_server},
        allowed_tools=["mcp__search__web_search"]
    )

    print("🤖 Starting agent with Claude Agent SDK...\n")

    # Create client and make query
    async with ClaudeSDKClient(options=options) as client:
        await client.query("Search the internet for 'claude code' and show me the top 3 results.")

        # Receive and print responses
        async for message in client.receive_response():
            print_message(message)

    print("\n✅ Agent finished!")


if __name__ == "__main__":
    asyncio.run(run_agent())