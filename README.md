# MagneticSphere AI
# 🧲 MagneticSphere AI

> Predict opportunities before competitors see them.

AI-powered multi-agent opportunity intelligence platform that continuously captures business signals, reasons over them using GraphRAG and LLMs, and autonomously triggers actions.

Detect. Reason. Predict. Act.

Multi-agent opportunity prediction platform .

MagneticSphere AI turns market signals into explainable opportunity scores, recommended actions, and generated outreach. The repository is structured as a production-shaped monorepo while keeping the default experience runnable with deterministic demo data.

## What It Does

- Captures business signals from news, funding, hiring, social, and tech-stack sources.
- Runs a sequential agent pipeline inspired by LangGraph.
- Builds explainable opportunity scores from evidence.
- Provides semantic retrieval and graph reasoning extension points for Qdrant and Neo4j.
- Generates suggested workflows, Slack alert copy, CRM updates, and outreach emails.
- Presents opportunities, trends, timelines, and relationship graphs in a dashboard.

## Repository Structure

```text
apps/
  api/        FastAPI backend and agent pipeline
  web/        Next.js dashboard
docs/         Architecture and demo guide
infra/        Docker Compose for app services and optional data stores
```

Full product and system documentation is available in `docs/PROJECT_DOCUMENTATION.md`.

## Quick Start

### Frontend

```bash
cd apps/web
npm install
npm run dev
```

Open `http://localhost:3000`.

### Backend

```bash
cd apps/api
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Open `http://localhost:8000/docs`.

The frontend uses demo data by default and can call the backend when `NEXT_PUBLIC_API_URL=http://localhost:8000` is set.

## Turning On Real Integrations

Copy `.env.example` to `apps/api/.env`, add credentials, then set:

```env
ENABLE_LIVE_INTEGRATIONS=true
```

Useful checks:

```bash
cd apps/api
uvicorn app.main:app --reload --port 8000
```

Open `http://localhost:8000/api/integrations/status` to see which providers are active.

Run the agent pipeline once:

```bash
python -m app.tasks.run_agents --once
```

Run continuously every 30 minutes:

```bash
python -m app.tasks.run_agents --interval 1800
```
┌──────────────┐
│ News Sources │
└──────┬───────┘
       ↓
┌────────────────┐
│ Signal Agents  │
└────────────────┘
       ↓
┌────────────────┐
│ LangGraph Flow │
└────────────────┘
       ↓
┌────────────────┐
│ Opportunity AI │
└────────────────┘
       ↓
┌──────────────┬───────────────┐
│ Slack Alerts │ HubSpot CRM   │
└──────────────┴───────────────┘


### Required Credentials

- `GEMINI_API_KEY`: Gemini reasoning and outreach generation.
- `SLACK_WEBHOOK_URL`: Slack alerts for high-intent opportunities.
- `HUBSPOT_ACCESS_TOKEN`: HubSpot company/deal creation.
- `QDRANT_URL` and optional `QDRANT_API_KEY`: semantic opportunity memory.
- `NEO4J_URI`, `NEO4J_USERNAME`, `NEO4J_PASSWORD`: knowledge graph storage.
- `NEWS_RSS_FEEDS`: comma-separated RSS feeds for live news signals.

## Demo Flow

1. Show top opportunities ranked by explainable score.
2. Open an opportunity and explain signals, confidence, graph relationships, and recommended next action.
3. Generate a personalized outreach email.
4. Show trend analysis and competitor sentiment.
5. Explain that demo adapters can be replaced by live News API, LinkedIn, BuiltWith, Qdrant, Neo4j, Slack, and CRM connectors.
