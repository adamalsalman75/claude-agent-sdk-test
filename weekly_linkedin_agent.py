"""
Weekly LinkedIn Article Generator using Claude Agent SDK

This agent:
1. Connects to your production MCP servers (finance, discovery, stem)
2. Retrieves the week's published articles from macrospire.com
3. Analyzes and consolidates key insights
4. Generates a compelling LinkedIn post summarizing the week's content

Compares to: Your Spring AI ContentOrchestrationService multi-agent workflow
"""

import asyncio
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions
from pprint import pprint

# OAuth2 token provider (same as before)
import requests
from typing import Optional

class OAuth2TokenProvider:
    """Obtains OAuth2 tokens from Spring Authorization Server."""

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

        response = requests.post(
            self.token_url,
            data={
                "grant_type": "client_credentials",
                "scope": "mcp:read mcp:write mcp:tools"
            },
            auth=(self.client_id, self.client_secret),
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        response.raise_for_status()

        token_data = response.json()
        self._token = token_data["access_token"]
        expires_in = token_data.get("expires_in", 3600)
        self._expires_at = datetime.now() + timedelta(seconds=expires_in - 60)

        return self._token


def print_message(message):
    """Pretty print messages."""
    print(f"\n{'=' * 80}")
    print(f"{type(message).__name__}:")
    print('=' * 80)
    message_dict = vars(message) if hasattr(message, '__dict__') else str(message)
    pprint(message_dict, width=120, compact=False)


async def generate_weekly_linkedin_article():
    """
    Generate a LinkedIn article consolidating the week's Macrospire content.

    This demonstrates Claude Agent SDK's autonomous workflow compared to
    Spring AI's manual multi-agent orchestration.
    """
    load_dotenv()

    # Setup OAuth2 for production MCP servers
    token_provider = OAuth2TokenProvider(
        token_url=os.getenv("AUTH_SERVER_TOKEN_URL"),
        client_id=os.getenv("MCP_CLIENT_ID"),
        client_secret=os.getenv("MCP_CLIENT_SECRET")
    )

    token = token_provider.get_token()
    print(f"✅ Obtained OAuth2 token from {os.getenv('AUTH_SERVER_TOKEN_URL')}")

    # Calculate date range for the past week
    today = datetime.now()
    week_ago = today - timedelta(days=7)
    date_range = f"{week_ago.strftime('%Y-%m-%d')} to {today.strftime('%Y-%m-%d')}"

    # Configure Claude Agent SDK with your production MCP servers
    options = ClaudeAgentOptions(
        model="claude-sonnet-4-5-20250929",
        mcp_servers={
            "finance": {
                "type": "http",
                "url": os.getenv("FINANCE_MCP_URL"),
                "headers": {"Authorization": f"Bearer {token}"}
            },
            "discovery": {
                "type": "http",
                "url": os.getenv("DISCOVERY_MCP_URL"),
                "headers": {"Authorization": f"Bearer {token}"}
            },
            "stem": {
                "type": "http",
                "url": os.getenv("STEM_MCP_URL"),
                "headers": {"Authorization": f"Bearer {token}"}
            }
        },
        # Allow tools from all MCP servers + built-in tools
        allowed_tools=[
            "mcp__finance__*",
            "mcp__discovery__*",
            "mcp__stem__*",
            "WebFetch",  # Built-in: fetch macrospire.com content
            "Read",      # Built-in: if needed
        ],
        system_prompt=f"""
        You are a content strategist for Macrospire, a multi-domain content platform
        covering finance, STEM, and discovery topics.

        Your task: Create a compelling LinkedIn article that consolidates this week's
        published content ({date_range}).

        IMPORTANT: Macrospire.com is the blog at https://macrospire.com. You should:
        1. Fetch the homepage or recent articles from macrospire.com
        2. Identify the key articles published in the past week
        3. Use the MCP tools (finance, discovery, stem) to enrich context if needed
        4. Write a LinkedIn-style article (3-5 paragraphs) that:
           - Highlights the week's most interesting insights
           - Connects themes across domains (finance + science + discovery)
           - Uses engaging language suitable for LinkedIn
           - Includes a call-to-action to visit macrospire.com

        Be autonomous: decide which tools to use and how to structure the research.
        """
    )

    print(f"\n🤖 Starting Weekly LinkedIn Article Generation")
    print(f"📅 Date Range: {date_range}")
    print(f"🔧 Connected to MCP Servers:")
    print(f"   - Finance: {os.getenv('FINANCE_MCP_URL')}")
    print(f"   - Discovery: {os.getenv('DISCOVERY_MCP_URL')}")
    print(f"   - STEM: {os.getenv('STEM_MCP_URL')}")
    print(f"\n{'=' * 80}\n")

    # Run the agent
    async with ClaudeSDKClient(options=options) as client:
        await client.query(f"""
        Generate a LinkedIn article consolidating Macrospire's content from the past week
        ({date_range}).

        Start by fetching recent articles from https://macrospire.com, then analyze
        and create an engaging summary.
        """)

        # Collect and display messages
        final_result = None
        async for message in client.receive_response():
            print_message(message)

            # Capture final result
            if type(message).__name__ == "ResultMessage":
                final_result = message

        # Display summary
        if final_result:
            print(f"\n{'=' * 80}")
            print("📊 GENERATION SUMMARY")
            print('=' * 80)
            print(f"✅ Status: {final_result.subtype}")
            print(f"⏱️  Duration: {final_result.duration_ms / 1000:.2f}s")
            print(f"💰 Cost: ${final_result.total_cost_usd:.4f}")
            print(f"🔄 Turns: {final_result.num_turns}")
            print(f"📝 Input tokens: {final_result.usage.get('input_tokens', 0)}")
            print(f"💾 Cached tokens: {final_result.usage.get('cache_read_input_tokens', 0)}")
            print(f"📤 Output tokens: {final_result.usage.get('output_tokens', 0)}")

            print(f"\n{'=' * 80}")
            print("📄 FINAL LINKEDIN ARTICLE")
            print('=' * 80)
            print(final_result.result)
            print('=' * 80)

            return final_result.result

        return None


async def main():
    """Run the weekly LinkedIn article generator."""
    try:
        article = await generate_weekly_linkedin_article()

        if article:
            # Optionally save to file
            output_file = f"linkedin_article_{datetime.now().strftime('%Y%m%d')}.md"
            with open(output_file, 'w') as f:
                f.write(article)
            print(f"\n✅ Article saved to: {output_file}")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())