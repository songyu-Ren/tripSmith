# TripSmith

TripSmith is an open-source travel planning copilot. Enter your trip requirements and preferences to generate 3 explainable options (budget/time/balanced), then generate a day-by-day itinerary and export it (ICS / Markdown).

## Feature overview

- Trip creation: origin/destination, dates, budget, travelers, preferences
- Constraint generation and confirmation: generate explainable constraints, then confirm before planning
- Plan generation (async job): includes progress, stage, and request_id
- Itinerary generation (async job): day-by-day, segmented by morning/afternoon/evening
- Saved plans: save a plan and generate an itinerary from saved plans
- Export: ICS calendar, Markdown itinerary
- Price alerts (MVP): mock price + scheduled checks + notification placeholder

## Run locally (Docker Compose)

1. Start services:

   ```bash
   docker compose up --build
   ```

2. Open:
   - Web: http://localhost:3000
   - API docs: http://localhost:8000/docs

The default provider/LLM is mock (works end-to-end without any keys). To enable real providers, copy `.env.example` to `.env` at the repository root and fill in the required keys.

## Run locally (without Docker)

### API

```bash
cd apps/api
python -m venv .venv
source .venv/bin/activate   # On Windows use: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn tripsmith.main:app --reload --port 8000
```

### Web

```bash
cd apps/web
npm install
npm run dev
```

## Tests and checks

### Backend

```bash
cd apps/api
pytest
ruff check .
```

### Frontend

```bash
cd apps/web
npm run typecheck
npm run lint
npm run build
```

## Smoke Test

This repository includes an end-to-end smoke test. It will `docker compose up -d`, generate a trip/plan/itinerary via the API, then validate the ICS output.

```bash
./scripts/smoke_test.sh
```

## Manual verification (3–6 steps)

1. Fill in the trip form on the home page → click “Generate plans”
2. On the results page, click “Generate constraints” → adjust → click “Confirm and continue”
3. Click “Regenerate plans” and watch the job stage/progress updates
4. Click “Save this plan” on any plan card, then see it appear in “Saved plans”
5. Click “Generate itinerary” and review the day-by-day itinerary segmented by time period
6. Click “Export ICS / Export Markdown” and verify the exported content
