# Architecture

## Runtime Flow

```text
Internet Signals
  News, Hiring, Funding, Social, GitHub, BuiltWith
        |
        v
Signal Agents
  Funding Agent, Hiring Agent, News Agent, Social Agent, Tech Stack Agent
        |
        v
Memory Layer
  PostgreSQL for records, Qdrant for semantic memory, Neo4j for relationships
        |
        v
Reasoning Agent
  Combines evidence and predicts buying intent
        |
        v
Opportunity Scoring Agent
  Score, confidence, reasons, risks, next best action
        |
        v
Workflow Agent
  Email, Slack alert, CRM update, meeting recommendation
        |
        v
Dashboard
```

## Backend Modules

- `app/agents`: Individual signal, retrieval, graph, reasoning, scoring, workflow, and monitoring agents.
- `app/services`: Orchestration and use-case services.
- `app/repositories`: Persistence adapters and demo data.
- `app/models`: Pydantic domain models shared across API responses.
- `app/api`: FastAPI routers.

## Hackathon Strategy

The implementation defaults to deterministic demo agents. This makes the project reliable on stage and avoids API quota failures. Each demo agent has a narrow interface so live integrations can replace it:

- News API or RSS can replace `NewsAgent`.
- Job board scraping or partner APIs can replace `HiringAgent`.
- Qdrant can replace the in-memory retrieval adapter.
- Neo4j can replace the static graph adapter.
- Gemini can replace the deterministic reasoning adapter.
- Slack, HubSpot, Salesforce, or n8n can replace the workflow adapter.

