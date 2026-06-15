# MagneticSphere AI API

FastAPI backend for the multi-agent opportunity pipeline.

## Run

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

The API reads environment variables from the repository `.env`, `apps/api/.env`, or the current process. Keep secrets in local `.env` files only.

## Endpoints

- `GET /api/health`
- `GET /api/integrations/status`
- `GET /api/agents/architecture`
- `POST /api/company/report`
- `GET /api/company/{company}`
- `GET /api/company/{company}/graph`
- `GET /api/company/{company}/timeline`
- `GET /api/company/{company}/agents`
- `GET /api/company/{company}/history`
- `GET /api/company/{company}/signals`
- `GET /api/reports/history`
- `POST /api/company/action`
- `POST /api/agents/run`
- `GET /api/opportunities`
- `GET /api/opportunities/{id}`
- `GET /api/trends`
- `POST /api/outreach`
