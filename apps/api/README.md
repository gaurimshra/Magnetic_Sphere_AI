# MagneticSphere AI API

FastAPI backend for the multi-agent opportunity pipeline.

## Run

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

## Endpoints

- `GET /api/health`
- `POST /api/agents/run`
- `GET /api/opportunities`
- `GET /api/opportunities/{id}`
- `GET /api/trends`
- `POST /api/outreach`

