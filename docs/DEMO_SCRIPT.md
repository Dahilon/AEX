# Demo Script (2 Minutes)

## Pre-Demo Checklist

- [ ] FastAPI backend running (signal mode = replay)
- [ ] Neo4j Aura instance seeded with graph data
- [ ] Datadog dashboard open in a browser tab
- [ ] UI loaded in browser, market table showing live prices
- [ ] MiniMax API key set (optional)
- [ ] TestSprite tests verified passing locally

## The 2-Minute Script

### 0:00-0:15 — Set the Stage
**Say**: "This is AEX — a real-time stock market for AI agents. Instead of trading stocks, you're trading AI agents. Their price is driven by real fundamentals — usage, performance, reliability — and by external shocks from the real world."

**Show**: The market table with 8 agents, live prices gently moving.

### 0:15-0:30 — Explain the Market
**Say**: "We have 8 agents across three sectors: Fraud & AML, Compliance, and Geo Intelligence. Each has real scores driving its valuation. Capital flows in and out based on agent quality and market events."

**Show**: Point to columns — price, sector, volatility, inflow. Highlight that CompliBot-EU is the top performer.

### 0:30-0:55 — Inject the Shock
**Say**: "Now watch what happens when we inject a real-world event. A regulation crackdown just dropped."

**Do**: Click "Inject Shock" → select "Regulation Crackdown"

**Say**: "Compliance agents surge — they benefit from regulation. Fraud and AML agents drop — tighter rules increase their risk profile. This uses a sector sensitivity matrix with shock propagation over multiple ticks."

**Show**: Prices moving in the table. Green arrows on Compliance, red on Fraud/AML.

### 0:55-1:15 — Show the Graph
**Say**: "But the real power is seeing HOW capital flows through the system."

**Do**: Click "Graph View" → Neo4j visualization loads

**Say**: "This is our capital contagion graph. Users allocate to capital pools, pools back agents, agents belong to sectors. When the regulation shock hit, you can see the contagion path — capital flowing OUT of Fraud/AML agents and INTO Compliance. The red edges show the impact path."

**Show**: Neo4j graph with highlighted contagion path. Point to thick edges = high capital flow.

### 1:15-1:35 — Bedrock Analysis
**Say**: "Let's ask our AI analyst — powered by Amazon Bedrock — to explain what just happened."

**Do**: Click "Run Analysis" (or type in CopilotKit: "Why did prices move?")

**Say**: "The Market Analyst ties the price movement to the specific shock, cites the metrics, and recommends a portfolio rebalancing. It uses tools to query the graph and market snapshot — not hallucinated data."

**Show**: Analysis text appearing in the chat panel. Point to specific citations.

### 1:35-1:50 — Datadog Dashboard
**Say**: "And everything is deeply observable."

**Do**: Switch to Datadog tab

**Say**: "Here's our market observatory dashboard. You can see the shock severity spike, agent prices diverging, volatility heating up, and cascade probability rising. Below that — full LLM telemetry: token usage, latency, and error rates for every Bedrock call. This isn't bolted-on monitoring — the market metrics ARE the observability."

**Show**: Dashboard with visible spikes correlating to the shock timing.

### 1:50-2:00 — Close Strong
**Say**: "AEX proves that AI agents can be valued, traded, and monitored like financial assets. Built on AWS Bedrock, visualized with Neo4j, observed with Datadog, and tested with TestSprite. Every layer tells a coherent story."

**(Optional)**: Click "Play Audio Summary" for MiniMax voice: "Today's AEX market saw a regulation shock..."

---

## Fallback Mode (If APIs Fail)

### Scenario: Live signals down
- Switch to replay mode: `SIGNAL_MODE=replay`
- Pre-recorded signals from S3 play on a timer
- Demo proceeds identically — judges won't know the difference

### Scenario: Neo4j down
- Show a pre-captured screenshot of the graph
- Say: "Here's the capital flow graph — we're showing a snapshot due to connectivity"
- Skip the live graph interaction

### Scenario: Bedrock throttled/down
- Show cached analysis from last successful run
- Say: "Here's the analysis from our last market cycle" and add "[cached]"

### Scenario: MiniMax down
- Skip voice entirely
- It's optional — don't even mention it failed

### Scenario: Datadog down
- Show a pre-captured screenshot of the dashboard
- Extremely unlikely since Datadog dashboard just reads metrics already sent

### Nuclear Fallback
If everything is down, we can run the entire demo locally:
- In-memory market engine with canned data
- Pre-recorded Bedrock responses
- Screenshot-based graph and dashboard
- This degrades the demo but still tells the story

## Demo Tips

1. **Practice the shock injection 3 times** before going live
2. **Pre-warm Bedrock** with a test call 5 min before demo to avoid cold start
3. **Have Datadog dashboard already zoomed** to the right time window
4. **Keep the Neo4j graph pre-loaded** — first load can be slow
5. **Talk over loading spinners** — never go silent waiting for an API
