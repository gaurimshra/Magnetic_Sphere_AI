# Production Integrations

## Activation Model

The backend is demo-safe by default. External providers are used only when:

```env
ENABLE_LIVE_INTEGRATIONS=true
```

and the required provider credential is present.

## Integration Status

Run the API and open:

```text
http://localhost:8000/api/integrations/status
```

This reports whether integrations are enabled, configured, and reachable. When `ENABLE_LIVE_INTEGRATIONS=true`, the endpoint runs lightweight connectivity checks against provider read/status endpoints where possible. It never returns credential values.

Notes:

- Slack bot tokens are checked with Slack `auth.test`.
- Slack webhook URLs are marked configured, but the health check is skipped because validating a webhook requires sending a message.
- `TARGET_COMPANIES_JSON` is validated locally as JSON instead of calling an external provider.

## Gemini

Used by:

- `ReasoningAgent`
- `WorkflowAgent.generate_email`

Environment:

```env
GEMINI_API_KEY=
GEMINI_MODEL=gemini-3.5-flash
```

If Gemini is unavailable, deterministic scoring and email generation are used.

## Qdrant

Used by:

- `RetrievalAgent`

Environment:

```env
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=
QDRANT_COLLECTION=opportunity_memory
VECTOR_SIZE=384
```

The current implementation uses a stable hash vectorizer so the vector database path works without a paid embedding model. Replace `HashVectorizer` with Gemini/OpenAI embeddings for stronger semantic retrieval.

## Neo4j

Used by:

- `KnowledgeGraphAgent`

Environment:

```env
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=
```

The adapter writes companies, technologies, and competitors, then reads relationship context for the dashboard graph.

## Slack

Used by:

- `WorkflowAgent.execute_actions`

Environment:

```env
SLACK_WEBHOOK_URL=
```

High-intent opportunities with score `>= 85` trigger an alert.

## HubSpot CRM

Used by:

- `WorkflowAgent.execute_actions`

Environment:

```env
HUBSPOT_ACCESS_TOKEN=
# Optional alias for older/local naming:
HUBSPOT_API_KEY=
HUBSPOT_BASE_URL=https://api.hubapi.com
```

The first implementation creates a company and deal. A production version should add deduplication, associations, custom properties, and retry handling.

## Live Signals

Used by:

- `RSSNewsAgent`
- `NewsAPIAgent`

Environment:

```env
NEWS_API_KEY=
NEWS_API_URL=https://newsapi.org/v2/everything
NEWS_API_PAGE_SIZE=20
NEWS_RSS_FEEDS=https://techcrunch.com/tag/artificial-intelligence/feed/,https://www.prnewswire.com/news-releases/news-releases-list.rss
TARGET_KEYWORDS=AI,MLOps,cloud AI,automation,healthcare AI,computer vision,funding,hiring
```

RSS runs without keys. NewsAPI is used when `NEWS_API_KEY` is present and live integrations are enabled. Add paid/vendor sources next for jobs, funding, firmographics, and intent data.

## Target Companies

By default the backend uses deterministic demo companies. For real-world runs, set `TARGET_COMPANIES_JSON` to a JSON array:

```env
TARGET_COMPANIES_JSON=[{"name":"Acme AI","domain":"acme.ai","industry":"Healthcare AI","region":"United States","stage":"Series A","technologies":["AWS","Kubernetes"],"competitors":["Example Competitor"]}]
```

Each object supports `id`, `name`, `website` or `domain`, `industry`, `region`, `stage`, `description`, `technologies`, and `competitors`.

## Dynamic Company Reports

The company intelligence API resolves a company query, gathers live signals, builds graph/timeline data, runs Gemini reasoning, stores the report, and returns a dashboard-ready payload.

Endpoints:

```text
POST /api/company/report
GET /api/company/{company}
GET /api/company/{company}/graph
GET /api/company/{company}/timeline
GET /api/company/{company}/history
GET /api/company/{company}/signals
GET /api/reports/history
POST /api/company/action
```

Request:

```json
{
  "query": "Tesla",
  "force_refresh": false
}
```

Report flow:

```text
Signal Agent
  -> News Agent
  -> Hiring Agent
  -> Social Sentiment Agent
  -> Tech Stack Agent
  -> Retrieval Agent
  -> Knowledge Graph Agent
  -> Reasoning Agent
  -> Opportunity Scoring Agent
  -> Workflow Agent
  -> Monitoring Agent
```

This flow is implemented with `langgraph.graph.StateGraph` in `apps/api/app/agents/company_langgraph.py`.
Each node receives shared report state, enriches it, and records execution metadata returned as `agent_steps`.

Local development falls back to `apps/api/app/company_reports.db` if PostgreSQL is unavailable. Production should run the Postgres service and install `psycopg[binary]`.

Raw provider evidence is stored separately in `company_signals` with raw payload JSON, source provenance, extracted entities, confidence, timestamps, and deduplication metadata. This gives reports durable evidence and lets the dashboard show score-change history and stored signals.

The initial seed list now covers OpenAI, Anthropic, Perplexity, Cursor, Reddit, Google Gemini, OpenCV, Computer Vision Market, Microsoft, and Notion.
