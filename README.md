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

### 1. Install Dependencies

Backend:

```bash
cd apps/api
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Frontend:

```bash
cd apps/web
npm install
```

### 2. Configure Local Environment

Copy the example file and keep real credentials local:

```bash
copy .env.example .env
```

The checked-in `.env.example` contains only blanks/placeholders. Do not commit `.env`.

For the full dashboard to call the API, keep:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### 3. Run The App

Backend:

```bash
cd apps/api
.venv\Scripts\activate
uvicorn app.main:app --reload --port 8000
```

Frontend:

```bash
cd apps/web
npm run dev
```

Open:

- `http://localhost:3000` for the dashboard.
- `http://localhost:3000/agents` for the LangGraph agent view.
- `http://localhost:3000/integrations` for integration health.
- `http://localhost:8000/docs` for the API docs.

The frontend can render fallback demo UI without the API, but the searchable company reports, history, raw evidence, actions, and integration status need the backend running.

Windows note: if Next.js fails because `NODE_OPTIONS` contains a VS Code debugger hook, run the frontend with:

```powershell
$env:NODE_OPTIONS = ""
npm.cmd run dev
```

## Verification

Useful checks before a demo or deployment:

```bash
cd apps/api
python -m compileall app
```

```powershell
cd apps/web
$env:NODE_OPTIONS = ""
$env:NODE_ENV = "production"
npm.cmd run build
```

```bash
curl http://localhost:8000/api/health
```

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

Optional local services are defined in `infra/docker-compose.yml`. Set `POSTGRES_PASSWORD` and `NEO4J_PASSWORD` in your local `.env` before running Docker Compose:

```bash
cd infra
docker compose up -d
```

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

## Current Limitations

- Funding, hiring, social sentiment, and private tech-stack data are partly inferred from news/GitHub unless paid/vendor APIs are added.
- Qdrant, Neo4j, PostgreSQL, Slack, HubSpot, NewsAPI, GitHub, and Gemini are optional and only used when configured.
- Report generation is synchronous today; a production deployment should add a background queue for long-running provider calls.
- There is not yet a formal automated test suite.

## Demo Flow

1. Show top opportunities ranked by explainable score.
2. Open an opportunity and explain signals, confidence, graph relationships, and recommended next action.
3. Generate a personalized outreach email.
4. Show trend analysis and competitor sentiment.
5. Explain that demo adapters can be replaced by live News API, LinkedIn, BuiltWith, Qdrant, Neo4j, Slack, and CRM connectors.
