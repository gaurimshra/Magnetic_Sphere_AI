# MagneticSphere AI Project Documentation

## Overview

MagneticSphere AI is a dynamic company intelligence and opportunity prediction platform. A user can search for a company such as `Tesla`, `OpenAI`, `Microsoft`, or `notion.so` and receive a live intelligence report that combines public signals, graph relationships, vector memory, and Gemini reasoning.

The application is built to answer:

- What is this company doing right now?
- Is it growing, hiring, raising money, launching products, or changing strategy?
- Which competitors, technologies, investors, and market signals matter?
- What opportunities exist for outreach, partnership, sales, or monitoring?
- Why did the system assign a specific opportunity score?

## What The App Is For

The platform is for sales, GTM, research, partnership, investment, and competitive-intelligence teams that need more than a static CRM record. It turns fragmented public signals into a structured report with explainable reasoning and next-best actions.

Example user journey:

1. User opens the dashboard.
2. User types a company name or domain.
3. Backend resolves the company to a normalized company object.
4. LangGraph agents collect live signals and enrich the state.
5. Gemini generates SWOT, risks, opportunities, and recommendations.
6. Qdrant and Neo4j are used when available for memory and graph context.
7. Report is cached in PostgreSQL when available, with SQLite fallback for local development.
8. Frontend renders score, graph, timeline, news, signals, competitors, technologies, and agent execution details.

## Current Tech Stack

Frontend:

- Next.js App Router
- React
- TypeScript
- Tailwind CSS
- Lucide icons
- React Flow for knowledge graph visualization
- Recharts for trend visualization

Backend:

- FastAPI
- Pydantic v2
- Pydantic Settings
- LangGraph `StateGraph`
- Gemini via `google-genai`
- HTTP integrations via `httpx`
- SQLite local fallback
- PostgreSQL support through `psycopg`
- Qdrant vector memory adapter
- Neo4j knowledge graph adapter

Infrastructure:

- Docker Compose for PostgreSQL, Redis, Qdrant, and Neo4j
- Local `.env` based configuration
- Ignored local secret files

External providers currently supported:

- Gemini API
- NewsAPI
- RSS feeds
- GitHub API
- Slack webhook or Slack bot token configuration
- HubSpot API token configuration
- Qdrant
- Neo4j
- PostgreSQL

## Core Features

Dynamic company search:

- Search by name or domain.
- Known company mappings exist for OpenAI, Anthropic, Perplexity, Cursor, Reddit, Google Gemini, OpenCV, Microsoft, Notion, Tesla, and Computer Vision Market.
- Unknown names are resolved with a best-effort domain guess.

Live signal collection:

- NewsAPI article search.
- RSS feed support.
- Funding/deal extraction from article text.
- Hiring signal extraction from article text.
- Social sentiment style extraction from public text.
- GitHub repository search for technology hints.

Company report generation:

- Company overview.
- Industry.
- Headquarters and employee placeholders when public data is unavailable.
- Recent news.
- Funding and acquisition signals.
- Hiring signals.
- Competitors.
- Technologies.
- Investors.
- Executive summary.
- SWOT analysis.
- Growth signals.
- Risks.
- Competitive landscape.
- Opportunities.
- AI recommendations.

Knowledge graph:

- Company to investors.
- Company to competitors.
- Company to technologies.
- Company to news.
- Company to hiring signals.
- Rendered in the frontend with React Flow.
- Written to Neo4j when Neo4j is running.

Vector memory:

- Company memory is embedded with the local hash vectorizer.
- Stored in Qdrant when Qdrant is running.
- Used as the basis for similar-company retrieval.

Caching and history:

- Reports are saved after generation.
- PostgreSQL is attempted first when configured.
- SQLite fallback is used locally at `apps/api/app/company_reports.db`.
- Cached reports return quickly.
- Force refresh can regenerate a report.
- Report history now includes score deltas, timeline deltas, and score-change alerts.

Raw signal storage:

- `company_signals` stores raw provider evidence as first-class records.
- Stored fields include provider, source URL, title, raw snippet, raw payload JSON, extracted entities, confidence, timestamps, and deduplication key.
- NewsAPI articles, Wikipedia overview payloads, GitHub repository evidence, and derived hiring/funding signals are persisted separately from generated report JSON.
- Reports can now be explained from saved evidence instead of only from the final generated payload.

Agent observability:

- Every company report now includes `agent_steps`.
- Each step has agent name, purpose, status, input summary, output summary, and duration.
- `/agents` frontend page shows the sequential architecture.
- Main dashboard shows the report pipeline for the current company.
- `/integrations` frontend page shows provider, database, vector DB, and graph health.
- Dashboard action controls let users manually send Slack alerts and create HubSpot records instead of automatically firing workflow actions.

## Unique Innovation

MagneticSphere AI is not just a dashboard and not just a chatbot. Its uniqueness comes from combining:

- Live company search.
- Multi-agent signal enrichment.
- LangGraph orchestration.
- GraphRAG-style company relationships.
- Explainable opportunity scoring.
- CRM and Slack workflow readiness.
- Report caching and history.
- Frontend visibility into what each agent did.

Traditional CRM systems usually store facts entered by humans. MagneticSphere AI actively watches signals, turns them into structured intelligence, reasons over them, and explains why a company is interesting now.

## System Architecture

High-level flow:

```text
User Search
  -> FastAPI /api/company/report
  -> LangGraph StateGraph
  -> Signal Agent
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
  -> Report Storage
  -> Frontend Dashboard
```

Primary backend files:

- `apps/api/app/main.py`: FastAPI application setup.
- `apps/api/app/api/routes.py`: API endpoints.
- `apps/api/app/core/config.py`: Environment settings.
- `apps/api/app/agents/company_langgraph.py`: LangGraph multi-agent workflow.
- `apps/api/app/services/company_intelligence_service.py`: Company intelligence business logic.
- `apps/api/app/repositories/company_report_repository.py`: PostgreSQL/SQLite report persistence.
- `apps/api/app/integrations/gemini_client.py`: Gemini reasoning and email generation.
- `apps/api/app/integrations/github_client.py`: GitHub repository search.
- `apps/api/app/integrations/qdrant_memory.py`: Vector memory.
- `apps/api/app/integrations/neo4j_graph.py`: Knowledge graph persistence.
- `apps/api/app/integrations/slack_client.py`: Slack alerts.
- `apps/api/app/integrations/hubspot_client.py`: HubSpot company/deal creation.

Primary frontend files:

- `apps/web/app/page.tsx`: Main dashboard page.
- `apps/web/app/agents/page.tsx`: Agent architecture page.
- `apps/web/components/Dashboard.tsx`: Searchable intelligence dashboard.
- `apps/web/lib/api.ts`: Frontend API client.
- `apps/web/lib/types.ts`: TypeScript contracts.

## LangGraph Agent Architecture

The system now uses `langgraph.graph.StateGraph` in `apps/api/app/agents/company_langgraph.py`.

### 1. Signal Agent

Purpose:

- Resolve the user query into company name and domain.
- Build cache key.
- Check for cached report unless force refresh is requested.

Why:

- Every downstream agent needs normalized company identity.
- Cache prevents repeated slow external calls.

### 2. News Agent

Purpose:

- Search NewsAPI for articles about the company.
- Fetch public overview where possible.
- Extract funding, acquisition, IPO, investment, and partnership signals from news.

Why:

- News provides real-time business context.

### 3. Hiring Agent

Purpose:

- Detect hiring signals from collected article text.
- Derive expansion indicators when direct jobs APIs are not available.

Why:

- Hiring usually indicates team expansion, new initiatives, and budget movement.

### 4. Social Sentiment Agent

Purpose:

- Extract public sentiment-like signals from available social/news text.
- Detect phrases related to pricing complaints, adoption, partnerships, or competitor pain.

Why:

- Public conversation can reveal dissatisfaction or buying intent.

### 5. Tech Stack Agent

Purpose:

- Detect technologies from news, overview text, and GitHub repository search.
- Identify tools such as AWS, Azure, GCP, Kubernetes, React, Python, PyTorch, Docker, PostgreSQL, and OpenCV.

Why:

- Technology fit makes recommendations more targeted and credible.

### 6. Retrieval Agent

Purpose:

- Write company memory to Qdrant when available.
- Prepare similar-company memory for future retrieval.

Why:

- The platform needs memory across reports and accounts.

### 7. Knowledge Graph Agent

Purpose:

- Build relationships between company, investors, competitors, technologies, news, and hiring.
- Write to Neo4j when available.

Why:

- Graph relationships make reasoning more explainable and navigable.

### 8. Reasoning Agent

Purpose:

- Use Gemini to combine evidence.
- Generate executive summary, SWOT, growth signals, risks, competitive landscape, opportunities, and AI recommendations.

Why:

- Raw signals need interpretation before they become useful intelligence.

### 9. Opportunity Scoring Agent

Purpose:

- Compute opportunity score and confidence.
- Use signal volume, graph/entity richness, and recommendation quality.

Why:

- Users need prioritization, not just data.

### 10. Workflow Agent

Purpose:

- Persist report.
- Prepare downstream workflow actions.
- Supports future Slack, HubSpot, outreach, and meeting scheduling expansion.

Why:

- Intelligence should drive action.

### 11. Monitoring Agent

Purpose:

- Finalize report freshness and timeline state.
- Attach completed agent execution metadata.

Why:

- Users need to see what happened and whether the report is fresh.

## API Endpoints

Health and status:

- `GET /api/health`
- `GET /api/integrations/status`

Agent architecture:

- `GET /api/agents/architecture`

Company intelligence:

- `POST /api/company/report`
- `GET /api/company/{company}`
- `GET /api/company/{company}/graph`
- `GET /api/company/{company}/timeline`
- `GET /api/company/{company}/agents`
- `GET /api/company/{company}/history`
- `GET /api/company/{company}/signals`
- `GET /api/reports/history`
- `POST /api/company/action`

Legacy/opportunity endpoints still available:

- `POST /api/agents/run`
- `GET /api/opportunities`
- `GET /api/opportunities/{opportunity_id}`
- `GET /api/trends`
- `POST /api/outreach`

## How Users Use It

Main dashboard:

1. Open `http://127.0.0.1:3000`.
2. Type a company name or domain.
3. Click Analyze.
4. Review opportunity score and confidence.
5. Read executive summary.
6. Inspect technologies, competitors, risks, and opportunities.
7. Open the knowledge graph.
8. Review timeline and live news.
9. Use recommendations to decide next actions.
10. Refresh the report when needed.

Agents page:

1. Open `http://127.0.0.1:3000/agents`.
2. Review the sequential agent architecture.
3. Understand each agent's purpose.
4. Return to the dashboard to run company reports.

## What Has Been Done

Completed so far:

- Built FastAPI backend.
- Built Next.js frontend.
- Added searchable company intelligence dashboard.
- Added LangGraph multi-agent workflow.
- Added Gemini reasoning.
- Added NewsAPI and RSS live signal support.
- Added GitHub token support and GitHub tech-stack signals.
- Added Qdrant adapter.
- Added Neo4j adapter.
- Added HubSpot adapter.
- Added Slack webhook/bot token config visibility.
- Added report persistence with PostgreSQL-first and SQLite fallback.
- Added report caching.
- Added report history foundation.
- Added graph and timeline endpoints.
- Added frontend `/agents` page.
- Added per-agent execution metadata.
- Added local target company seed list.
- Verified backend compile.
- Verified frontend production build.
- Verified local servers.

## What Was Being Done Most Recently

The most recent work converted the company report pipeline from manual service orchestration into a real LangGraph `StateGraph`.

This added:

- Named agent nodes.
- Sequential state passing.
- Agent execution summaries.
- Agent duration tracking.
- Frontend visibility into the agent workflow.
- `/api/agents/architecture`.
- `/api/company/{company}/agents`.
- `/agents` frontend page.

Then the new credentials were added to local config:

- GitHub token.
- HubSpot API key.
- Slack bot token.

GitHub was also connected to the Tech Stack Agent for repository-based technology hints.

## What Should Improve Next

Data quality:

- Add Crunchbase or Dealroom API for funding, investors, acquisitions, and valuations.
- Add BuiltWith or Wappalyzer API for accurate tech-stack detection.
- Add LinkedIn or a compliant jobs API for hiring trends.
- Add Twitter/X or social-listening API for sentiment.
- Add financial market API for public-company revenue, market cap, and valuation.
- Add company-domain resolution API such as Clearbit-style enrichment if available.

Reliability:

- Add background job queue for long report generation.
- Add retry policies per provider.
- Add provider-level rate-limit handling.
- Add structured error reporting per agent.
- Add test suite around graph nodes.

Product:

- Add report history page.
- Add company comparison view.
- Add watchlists.
- Add alerts for score changes.
- Add export to PDF.
- Add user accounts and saved companies.
- Add admin integration settings page.

AI:

- Add stronger embedding model instead of hash vectorizer.
- GraphRAG context now pulls Neo4j relationship context and Qdrant similar-company memory into Gemini prompts when those stores are reachable.
- Add stronger path-ranking and citation-aware retrieval over Neo4j and Qdrant.
- Add citation-aware Gemini output.
- Add confidence scoring per claim.

Security:

- Move all secrets to a secrets manager in production.
- Rotate credentials pasted in chat.
- Add provider permission scopes documentation.
- Add audit logs for workflow actions.

## What I Am Going To Do Next

Recommended next implementation steps:

1. Add true provider connectors for funding, tech stack, and jobs.
2. Add a background job system so report generation does not block HTTP requests.
3. Add report history UI and cached report browser.
4. Add provider health checks that test actual connectivity, not only whether a key exists.
5. Add richer GraphRAG reasoning using Neo4j paths plus Qdrant retrieval.
6. Add Slack and HubSpot action controls in the UI so users choose when to send alerts or create CRM records.

## Current Limitations

- LinkedIn, Twitter/X, Crunchbase, BuiltWith, and job portals are architecture responsibilities but not fully connected until provider APIs or approved data sources are available.
- GitHub is now connected, but GitHub does not prove a company's private stack. It gives public repository signals only.
- NewsAPI may miss paywalled or private company data.
- Gemini can reason over provided evidence, but precise financials require financial/funding data providers.
- Qdrant and Neo4j need their Docker services running for full storage behavior.

## Local Run

Backend:

```bash
cd apps/api
uvicorn app.main:app --reload --port 8000
```

Frontend:

```bash
cd apps/web
npm run dev
```

Open:

```text
http://127.0.0.1:3000
http://127.0.0.1:3000/agents
http://127.0.0.1:8000/docs
```

Optional services:

```bash
cd infra
docker compose up -d
```
