# Weekly LinkedIn Article: Spring AI vs Claude Agent SDK

## Use Case

**Goal**: Automatically generate a LinkedIn article every week that consolidates the content published on macrospire.com by the `content-engine` daily cron job.

**Workflow**:
1. Fetch last week's articles from macrospire.com
2. Analyze key themes and insights across finance, STEM, and discovery domains
3. Generate an engaging LinkedIn post (3-5 paragraphs)
4. Include call-to-action to visit macrospire.com

## Current Implementation (Spring AI)

Your Spring AI implementation would use the manual multi-agent orchestration pattern from `ContentOrchestrationService`:

```java
@Service
public class WeeklyLinkedInService {

    private final ChatClient chatClient;
    private final McpClientMcpTransport financeTransport;
    private final McpClientMcpTransport discoveryTransport;
    private final McpClientMcpTransport stemTransport;

    public String generateWeeklyLinkedInArticle() {
        // Step 1: Fetch recent articles from macrospire.com
        var recentArticles = fetchRecentArticlesAgent.fetch();

        // Step 2: Analyze content with MCP tools
        var financeInsights = analyzeFinanceAgent.analyze(recentArticles);
        var discoveryInsights = analyzeDiscoveryAgent.analyze(recentArticles);
        var stemInsights = analyzeStemAgent.analyze(recentArticles);

        // Step 3: Draft LinkedIn post
        var draft = draftAgent.createLinkedInDraft(
            recentArticles,
            financeInsights,
            discoveryInsights,
            stemInsights
        );

        // Step 4: Enhance and finalize
        var finalPost = enhanceAgent.enhance(draft);

        return finalPost;
    }
}
```

**Characteristics:**
- ✅ Explicit, predictable workflow
- ✅ Clear separation of concerns (each agent has one job)
- ✅ Easy to debug (step-by-step)
- ❌ Rigid structure (hard to adapt to different content types)
- ❌ ~300+ lines of boilerplate (multiple agent classes)
- ❌ Manual tool routing and result handling
- ❌ Separate API calls per agent (higher cost, no caching between steps)

## New Implementation (Claude Agent SDK)

The new `weekly_linkedin_agent.py` uses Claude Agent SDK:

```python
async def generate_weekly_linkedin_article():
    # Configure MCP servers and system prompt
    options = ClaudeAgentOptions(
        mcp_servers={
            "finance": {"type": "http", "url": finance_url, "headers": auth},
            "discovery": {"type": "http", "url": discovery_url, "headers": auth},
            "stem": {"type": "http", "url": stem_url, "headers": auth}
        },
        system_prompt="""
        You are a content strategist for Macrospire.

        Create a LinkedIn article consolidating this week's content.
        Be autonomous: fetch macrospire.com, use MCP tools, write the article.
        """
    )

    # Run agent - it decides the workflow!
    async with ClaudeSDKClient(options=options) as client:
        await client.query("Generate weekly LinkedIn article from macrospire.com")

        async for message in client.receive_response():
            if type(message).__name__ == "ResultMessage":
                return message.result
```

**Characteristics:**
- ✅ ~100 lines total (vs 300+ in Spring AI)
- ✅ Flexible workflow (Claude decides which tools to use)
- ✅ Single conversation with prompt caching (lower cost)
- ✅ Automatic error handling and retries
- ✅ Easy to modify (change prompt, not code)
- ❌ Less explicit control (Claude decides the steps)
- ❌ Harder to debug (can't breakpoint between agent steps)

## Key Differences

### 1. Workflow Definition

**Spring AI:**
```java
// Explicit, hard-coded steps
var articles = step1();
var insights = step2(articles);
var draft = step3(insights);
var final = step4(draft);
```

**Claude Agent SDK:**
```python
# Implicit, AI-driven workflow described in prompt
system_prompt = """
Fetch articles → Analyze → Write LinkedIn post
Use whatever tools you need autonomously
"""
```

### 2. Tool Usage

**Spring AI:**
```java
// Developer decides which tools each agent uses
@Service
public class FinanceAnalysisAgent {
    // This agent only has finance MCP tools
    private ChatClient financeOnlyClient;
}
```

**Claude Agent SDK:**
```python
# Claude decides which tools to use
allowed_tools=[
    "mcp__finance__*",
    "mcp__discovery__*",
    "mcp__stem__*",
    "WebFetch"
]
# Claude autonomously selects relevant tools
```

### 3. Error Handling

**Spring AI:**
```java
try {
    var articles = fetchAgent.fetch();
    if (articles.isEmpty()) {
        return fallbackArticle();
    }
    // Manual error handling at each step
} catch (Exception e) {
    log.error("Failed", e);
    return fallbackArticle();
}
```

**Claude Agent SDK:**
```python
# Built-in error handling
# If WebFetch fails, Claude might try alternative approaches
# If a tool returns error, Claude adapts
```

### 4. Cost & Performance

**Spring AI (Current):**
```
Fetch Agent:       500 tokens   (no caching)
Finance Agent:    2000 tokens   (no caching)
Discovery Agent:  2000 tokens   (no caching)
STEM Agent:       2000 tokens   (no caching)
Draft Agent:      3000 tokens   (no caching)
Enhance Agent:    2000 tokens   (no caching)
---
Total: 11,500 tokens, 6 separate API calls
Cost: ~$0.08-0.12 per generation
```

**Claude Agent SDK (New):**
```
Single conversation:
- Tool schemas:    5000 tokens   (cached after first call)
- First call:      6500 tokens
- Subsequent:      1500 tokens   (90% cached)
---
First run: 6,500 tokens, 1 conversation
Later runs: 1,500 tokens (prompt caching)
Cost: ~$0.05 first run, ~$0.01 subsequent
```

## Running the Comparison

### Spring AI Version (Current)
```bash
# In your ai-content-engine project
cd content-engine
./mvnw spring-boot:run

# Trigger via API or scheduled job
curl -X POST http://localhost:8080/api/linkedin/weekly-article
```

### Claude Agent SDK Version (New)
```bash
# In this test project
cd claude-agent-sdk-test

# Set up .env with production credentials
cat > .env << EOF
AUTH_SERVER_TOKEN_URL=https://auth.macrospire.com/oauth2/token
MCP_CLIENT_ID=<your-client-id>
MCP_CLIENT_SECRET=<your-client-secret>
FINANCE_MCP_URL=https://finance.macrospire.com/mcp
DISCOVERY_MCP_URL=https://discovery.macrospire.com/mcp
STEM_MCP_URL=https://stem.macrospire.com/mcp
ANTHROPIC_API_KEY=<your-api-key>
EOF

# Run the agent
uv run python weekly_linkedin_agent.py
```

## Expected Output

The agent will:
1. **Fetch macrospire.com** using built-in WebFetch tool
2. **Identify recent articles** (published in past 7 days)
3. **Use MCP tools** to enrich context:
   - Finance tools: get market data, earnings info
   - Discovery tools: fetch RSS feeds, search academic papers
   - STEM tools: get NASA data, environmental info
4. **Generate LinkedIn article** consolidating key insights
5. **Save to file**: `linkedin_article_YYYYMMDD.md`

Example output:
```
🤖 Starting Weekly LinkedIn Article Generation
📅 Date Range: 2025-09-29 to 2025-10-06
🔧 Connected to MCP Servers:
   - Finance: https://finance.macrospire.com/mcp
   - Discovery: https://discovery.macrospire.com/mcp
   - STEM: https://stem.macrospire.com/mcp

================================================================================
SystemMessage:
================================================================================
'tools': ['Task', 'Bash', 'WebFetch', 'Read', 'Write',
          'mcp__finance__*', 'mcp__discovery__*', 'mcp__stem__*']

================================================================================
AssistantMessage:
================================================================================
"I'll fetch the recent articles from macrospire.com..."

================================================================================
ToolUseBlock:
================================================================================
name='WebFetch', input={'url': 'https://macrospire.com'}

[... more tool uses and analysis ...]

================================================================================
📄 FINAL LINKEDIN ARTICLE
================================================================================
This Week at Macrospire: Where Finance Meets Innovation

Last week brought fascinating convergence across our coverage areas...

[3-5 engaging paragraphs with insights from the week's articles]

Ready to dive deeper? Visit macrospire.com for full analyses.
================================================================================

📊 GENERATION SUMMARY
✅ Status: success
⏱️  Duration: 12.5s
💰 Cost: $0.0523
🔄 Turns: 6
📝 Input tokens: 12
💾 Cached tokens: 24,567
📤 Output tokens: 456

✅ Article saved to: linkedin_article_20251006.md
```

## Evaluation Criteria

Compare both implementations on:

### 1. **Output Quality**
- ❓ Which generates more engaging LinkedIn content?
- ❓ Which better consolidates multi-domain insights?
- ❓ Which has better tone/style for LinkedIn audience?

### 2. **Development Speed**
- ⏱️ Time to implement: Spring AI (~2-3 days) vs Claude SDK (~2 hours)
- ⏱️ Time to modify workflow: Spring AI (code + test) vs Claude SDK (prompt)

### 3. **Cost**
- 💰 Per generation: ~$0.10 (Spring AI) vs ~$0.05 first/$0.01 subsequent (Claude SDK)
- 💰 Monthly (4 articles): ~$0.40 (Spring AI) vs ~$0.08 (Claude SDK)

### 4. **Reliability**
- 🔄 How often does it succeed on first try?
- 🔄 How does it handle missing articles?
- 🔄 How does it handle MCP server errors?

### 5. **Maintainability**
- 🛠️ How easy to add new content sources?
- 🛠️ How easy to change LinkedIn format?
- 🛠️ How easy to debug when things go wrong?

### 6. **Flexibility**
- 🔀 Can it adapt to different article types (finance-heavy vs STEM-heavy)?
- 🔀 Can it handle weeks with 2 articles vs 10 articles?
- 🔀 Can it adjust tone for different platforms (LinkedIn vs Twitter)?

## Recommendation

**For this use case, I'd recommend:**

✅ **Start with Claude Agent SDK** because:
- Quick to implement and iterate
- Autonomous workflow adapts to varying content
- Lower cost with prompt caching
- Easy to experiment with different prompts

✅ **Keep Spring AI** for:
- Production content generation (proven reliability)
- Cases where you need exact workflow control
- Integration with your existing Spring ecosystem

**Hybrid approach:**
- Use Claude Agent SDK for **experimental features** (like weekly LinkedIn)
- Keep Spring AI for **core content generation** (daily articles)
- Gradually migrate based on results

## Next Steps

1. ✅ Run `weekly_linkedin_agent.py` against production
2. ✅ Compare output with what you'd expect from Spring AI
3. ✅ Measure cost/performance over 4 weeks
4. ✅ Decide: migrate, hybrid, or stay with Spring AI

The data will tell you which approach works best for your specific use case!