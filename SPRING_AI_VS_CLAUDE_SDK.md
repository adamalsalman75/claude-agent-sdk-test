# Spring AI vs Claude Agent SDK: Agentic Flow Comparison

## Overview

This document compares building agentic workflows using **Spring AI** (your current Java implementation) versus **Claude Agent SDK** (new Python approach), both using your existing MCP infrastructure.

## Your Current Spring AI Implementation

### Architecture
```
┌─────────────────────────────────────────────────────┐
│  Content Engine (Spring Boot)                       │
│                                                      │
│  ┌────────────────────────────────────────────────┐ │
│  │  ContentOrchestrationService.java              │ │
│  │                                                 │ │
│  │  Manual Agentic Loop:                          │ │
│  │  1. NextArticleDecisionAgent (decides topic)   │ │
│  │  2. DiscoveryAgent (research via MCP)          │ │
│  │  3. DraftAgent (write draft)                   │ │
│  │  4. EnhanceAgent (improve content)             │ │
│  │  5. Save to DB                                 │ │
│  └────────────────────────────────────────────────┘ │
│               ↓                                      │
│  ┌────────────────────────────────────────────────┐ │
│  │  Spring AI ChatClient                          │ │
│  │  - AdvisorsConfig for MCP tools                │ │
│  │  - Manual tool execution                       │ │
│  │  - Manual conversation management              │ │
│  └────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────┘
                        ↓
              OAuth2 Token Provider
                        ↓
        ┌───────────────┴────────────────┐
        ↓                                ↓
Finance MCP (8081)              Discovery MCP (8084)
```

### Current Code Pattern (Spring AI)

**From your `ContentOrchestrationService.java`:**

```java
// Manual multi-agent orchestration
public void orchestrateContentGeneration() {
    // Step 1: Decision Agent
    var topic = nextArticleDecisionAgent.decideTopic();

    // Step 2: Discovery Agent (uses MCP tools)
    var research = discoveryAgent.research(topic);

    // Step 3: Draft Agent
    var draft = draftAgent.writeDraft(topic, research);

    // Step 4: Enhance Agent
    var final = enhanceAgent.enhance(draft);

    // Step 5: Save
    repository.save(final);
}
```

**Spring AI MCP Client Config:**

```java
@Bean
public List<NamedClientMcpTransport> namedClientMcpTransports() {
    List<NamedClientMcpTransport> transports = new ArrayList<>();

    // Manual transport creation with OAuth2
    addTransport(transports, "finance-mcp-server", financeMcpUrl);
    addTransport(transports, "discovery-mcp-server", discoveryMcpUrl);

    return transports;
}
```

## New Claude Agent SDK Implementation

### Architecture
```
┌─────────────────────────────────────────────────────┐
│  Python Agent (Claude Agent SDK)                    │
│                                                      │
│  ┌────────────────────────────────────────────────┐ │
│  │  ClaudeSDKClient                               │ │
│  │                                                 │ │
│  │  Automatic Agentic Loop:                       │ │
│  │  - Claude decides workflow steps               │ │
│  │  - Auto tool selection & execution             │ │
│  │  - Auto conversation management                │ │
│  │  - Built-in context tracking                   │ │
│  │  - Sub-agent spawning (Task tool)              │ │
│  └────────────────────────────────────────────────┘ │
│               ↓                                      │
│  ┌────────────────────────────────────────────────┐ │
│  │  MCP Servers Config                            │ │
│  │  - Simple dict configuration                   │ │
│  │  - Headers for OAuth2                          │ │
│  │  - Automatic tool discovery                    │ │
│  └────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────┘
                        ↓
              OAuth2 Token Provider (Python)
                        ↓
        ┌───────────────┴────────────────┐
        ↓                                ↓
Finance MCP (8081)              Discovery MCP (8084)
```

### New Code Pattern (Claude Agent SDK)

```python
# oauth_token_provider.py
class OAuth2TokenProvider:
    """Same OAuth2 flow as your Java client"""
    def __init__(self, token_url, client_id, client_secret):
        self.token_url = token_url
        self.client_id = client_id
        self.client_secret = client_secret

    def get_token(self):
        # Request token from your Spring Authorization Server
        # ... (same logic as your Java OAuth2McpTokenProvider)
```

```python
# content_agent.py
import asyncio
from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions
from oauth_token_provider import OAuth2TokenProvider

async def generate_article(topic: str):
    """
    Automatic multi-step agentic workflow.
    Claude decides the steps autonomously!
    """

    token_provider = OAuth2TokenProvider(
        token_url="http://localhost:9090/oauth2/token",
        client_id="python-agent",
        client_secret="secret"
    )

    options = ClaudeAgentOptions(
        mcp_servers={
            "finance": {
                "type": "http",
                "url": "http://localhost:8081/mcp",
                "headers": {"Authorization": f"Bearer {token_provider.get_token()}"}
            },
            "discovery": {
                "type": "http",
                "url": "http://localhost:8084/mcp",
                "headers": {"Authorization": f"Bearer {token_provider.get_token()}"}
            }
        },
        # Let Claude use all tools
        allowed_tools=["mcp__finance__*", "mcp__discovery__*"],

        # Optional: Define system prompt for content generation workflow
        system_prompt=f"""
        You are an AI content generation agent. Your task is to create a
        comprehensive article about {topic}.

        Follow this workflow:
        1. Research the topic using finance and discovery tools
        2. Find relevant data, news, and academic sources
        3. Write a well-structured draft
        4. Enhance it with additional insights
        5. Return the final article in markdown format
        """
    )

    async with ClaudeSDKClient(options=options) as client:
        await client.query(f"Create a comprehensive article about: {topic}")

        async for message in client.receive_response():
            if type(message).__name__ == "ResultMessage":
                return message.result  # Final article
```

## Key Differences

### 1. **Orchestration Control**

| Aspect | Spring AI (Current) | Claude Agent SDK (New) |
|--------|---------------------|------------------------|
| **Workflow Definition** | Manual, explicit steps in Java | Implicit, described in system prompt |
| **Agent Sequencing** | Hard-coded order | Claude decides dynamically |
| **Tool Selection** | Developer chooses which tools each agent can use | Claude auto-selects from available tools |
| **Error Handling** | Manual try/catch for each step | SDK handles retries and errors |
| **Context Passing** | Manual between agents | Automatic conversation context |

**Spring AI:**
```java
// Rigid, predefined workflow
var topic = decisionAgent.decide();      // Step 1
var research = discoveryAgent.research(topic);  // Step 2
var draft = draftAgent.draft(research);         // Step 3
var final = enhanceAgent.enhance(draft);        // Step 4
```

**Claude Agent SDK:**
```python
# Flexible, AI-driven workflow
await client.query("""
Create an article about {topic}.
Research thoroughly, then write a comprehensive draft.
""")
# Claude autonomously:
# - Decides which tools to use
# - Determines order of operations
# - Handles intermediate steps
# - Manages context between steps
```

### 2. **Tool Management**

| Aspect | Spring AI | Claude Agent SDK |
|--------|-----------|------------------|
| **Tool Registration** | Manual `ToolCallbackProvider` beans | Automatic via MCP server |
| **Tool Filtering** | Advisor-based per ChatClient | `allowed_tools` list |
| **Tool Discovery** | Compile-time configuration | Runtime discovery from MCP |
| **Tool Documentation** | Spring AI function descriptions | MCP tool schemas |

### 3. **Multi-Agent Workflows**

**Spring AI Approach (Manual):**
```java
// You define each agent and their interactions
@Service
public class DiscoveryAgent {
    private final ChatClient chatClient;

    public Research research(String topic) {
        return chatClient.prompt()
            .user(topic)
            .advisors(mcpAdvisor)  // Manually wire MCP tools
            .call()
            .entity(Research.class);
    }
}

@Service
public class DraftAgent {
    public Draft write(Research research) {
        // Manual orchestration
    }
}
```

**Claude Agent SDK Approach (Automatic):**
```python
# Option 1: Single agent with complex prompt
await client.query("""
Research {topic}, then write a draft, then enhance it.
""")

# Option 2: Sub-agents via Task tool (built-in)
options = ClaudeAgentOptions(
    allowed_tools=["Task", "mcp__finance__*", "mcp__discovery__*"],
    system_prompt="""
    You can spawn specialized sub-agents using the Task tool.
    Use one agent for research, another for writing.
    """
)
# Claude spawns sub-agents autonomously!
```

### 4. **Code Complexity**

**Spring AI Implementation (Your Current):**
- ~500+ lines for orchestration service
- Multiple agent classes
- Manual tool wiring in config
- Manual conversation management
- Explicit error handling
- State management between agents

**Claude Agent SDK Implementation (New):**
- ~100 lines for full workflow
- Single client with system prompt
- Automatic tool discovery
- Auto conversation management
- Built-in error handling
- Automatic context tracking

### 5. **Flexibility & Adaptability**

| Scenario | Spring AI | Claude Agent SDK |
|----------|-----------|------------------|
| **Add new tool** | Update config, redeploy | Just add to MCP server, auto-discovered |
| **Change workflow** | Modify Java code | Update system prompt |
| **A/B test workflows** | Deploy multiple versions | Pass different prompts |
| **Handle edge cases** | Write explicit code | Claude adapts autonomously |

### 6. **Debugging & Observability**

**Spring AI:**
- Standard Java logging
- Breakpoints in IDE
- Explicit step tracking
- Clear call stack

**Claude Agent SDK:**
- Message stream inspection
- `ResultMessage` with metrics (cost, tokens, duration)
- Tool use blocks show decisions
- Less control over internals

### 7. **Performance Characteristics**

| Metric | Spring AI | Claude Agent SDK |
|--------|-----------|------------------|
| **Latency** | Synchronous steps | Async operations |
| **Token Usage** | Separate calls per agent | Single conversation (prompt caching) |
| **Memory** | JVM heap | Python async (lighter) |
| **Concurrency** | Virtual threads | asyncio |
| **Cost** | N separate API calls | Optimized with caching |

## Comparison Example: Article Generation

### Task: "Create a financial analysis article about Apple's Q4 earnings"

#### Spring AI Implementation (Current)

```java
public Article generateFinanceArticle(String company, String quarter) {
    try {
        // Step 1: Decision (which aspects to cover)
        var aspects = decisionAgent.decideAspects(company, quarter);

        // Step 2: Gather earnings data (Finance MCP)
        var earnings = financeAgent.getEarnings(company, quarter);

        // Step 3: Find news context (Discovery MCP)
        var news = discoveryAgent.findNews(company, quarter);

        // Step 4: Draft article
        var draft = draftAgent.writeDraft(aspects, earnings, news);

        // Step 5: Enhance with analysis
        var enhanced = enhanceAgent.enhance(draft);

        // Step 6: Save
        return repository.save(enhanced);

    } catch (Exception e) {
        log.error("Article generation failed", e);
        return fallbackArticle();
    }
}
```

**Characteristics:**
- ✅ Predictable, testable
- ✅ Clear separation of concerns
- ✅ Java type safety
- ❌ Rigid workflow
- ❌ ~200 lines of orchestration code
- ❌ Manual error handling

#### Claude Agent SDK Implementation (New)

```python
async def generate_finance_article(company: str, quarter: str):
    token = token_provider.get_token()

    options = ClaudeAgentOptions(
        mcp_servers={
            "finance": {
                "type": "http",
                "url": "http://localhost:8081/mcp",
                "headers": {"Authorization": f"Bearer {token}"}
            },
            "discovery": {
                "type": "http",
                "url": "http://localhost:8084/mcp",
                "headers": {"Authorization": f"Bearer {token}"}
            }
        },
        allowed_tools=["mcp__finance__*", "mcp__discovery__*"],
        system_prompt=f"""
        You are a financial analyst. Create a comprehensive analysis
        article about {company}'s {quarter} earnings.

        Use the finance tools to get earnings data, financial metrics,
        and stock performance. Use discovery tools to find relevant
        news and context. Write a professional, data-driven article.
        """
    )

    async with ClaudeSDKClient(options=options) as client:
        await client.query(
            f"Create a detailed financial analysis article about "
            f"{company}'s {quarter} earnings performance"
        )

        async for message in client.receive_response():
            if type(message).__name__ == "ResultMessage":
                print(f"Cost: ${message.total_cost_usd:.4f}")
                print(f"Tokens: {message.usage}")
                return message.result
```

**Characteristics:**
- ✅ Flexible, adaptive workflow
- ✅ ~50 lines total
- ✅ Auto error handling
- ✅ Prompt caching saves cost
- ❌ Less explicit control
- ❌ Python (vs your Java stack)

## When to Use Each

### Use Spring AI (Current) When:
1. ✅ You need **deterministic workflows** with exact step control
2. ✅ **Type safety** and compile-time checks are critical
3. ✅ You want to **unit test** each agent step independently
4. ✅ Your team is **Java-focused**
5. ✅ You need **tight integration** with Spring ecosystem (DB, security, etc.)
6. ✅ Workflow is **stable and well-defined**
7. ✅ You want **full stack traces** for debugging

### Use Claude Agent SDK (New) When:
1. ✅ You want **AI-driven workflow decisions**
2. ✅ Workflow needs to **adapt to different inputs**
3. ✅ You want to **experiment quickly** with different approaches
4. ✅ **Prompt engineering** > rigid code structure
5. ✅ You value **conciseness** over explicitness
6. ✅ Cost optimization via **prompt caching** matters
7. ✅ You want **autonomous sub-agent spawning**

## Hybrid Approach

You could use **both**:

```java
// Spring Boot controller
@RestController
public class ArticleController {

    @Autowired
    private PythonAgentService pythonAgent;  // Calls Claude Agent SDK

    @Autowired
    private SpringAIOrchestrator javaAgent;  // Your current implementation

    @PostMapping("/articles/generate")
    public Article generateArticle(@RequestBody ArticleRequest req) {
        if (req.isExperimentalMode()) {
            // Use Claude Agent SDK for flexibility
            return pythonAgent.generate(req);
        } else {
            // Use Spring AI for production stability
            return javaAgent.orchestrate(req);
        }
    }
}
```

## Migration Strategy

If you want to experiment with Claude Agent SDK:

### Phase 1: Parallel Testing
1. Keep Spring AI as production
2. Build Claude Agent SDK version
3. Run both, compare outputs
4. A/B test with small percentage

### Phase 2: Selective Adoption
1. Use Claude Agent SDK for **experimental workflows**
2. Keep Spring AI for **critical production flows**
3. Measure: quality, cost, latency

### Phase 3: Decision
Based on results:
- **Option A**: Migrate fully to Claude Agent SDK
- **Option B**: Keep Spring AI, use Claude SDK for specific use cases
- **Option C**: Stay with Spring AI if results don't justify change

## Cost Analysis

### Spring AI (Current)
```
Decision Agent:     1 API call   →  ~500 tokens
Discovery Agent:    1 API call   →  ~2000 tokens (with tool use)
Draft Agent:        1 API call   →  ~3000 tokens
Enhance Agent:      1 API call   →  ~2000 tokens
---
Total: 4 separate API calls
Total tokens: ~7500 (no prompt caching between calls)
```

### Claude Agent SDK (New)
```
Single conversation with:
- Initial prompt:    ~500 tokens (cached)
- Tool schemas:      ~3000 tokens (cached from MCP)
- Tool results:      ~2000 tokens
- Claude responses:  ~2000 tokens
---
Total: 1 conversation, multiple turns
Total tokens: ~7500, but with prompt caching:
  - First call: ~7500 tokens
  - Subsequent calls: ~2000 tokens (90% cached)
```

**Cost savings**: ~70% on repeated workflows due to prompt caching

## Conclusion

**For Your Use Case:**

Since you want to **experiment** and **compare**, here's my recommendation:

1. **Build the Claude Agent SDK version** in this test project
2. **Keep your Spring AI implementation** in production (ai-content-engine)
3. **Run parallel tests** with same prompts/topics
4. **Compare**:
   - Output quality
   - Code maintainability
   - Cost per article
   - Development speed for new features
   - Error handling & reliability

**Hypothesis to test:**
- Claude Agent SDK will be **faster to modify** (change prompts vs code)
- Spring AI will be **more predictable** (explicit steps)
- Claude Agent SDK might **produce more creative** workflows
- Spring AI will be **easier to debug** when things go wrong

The beauty is: **Both can use your same MCP infrastructure**, so it's a fair comparison of the orchestration layer only!