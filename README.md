# StipendScout

Autonomous internship application agent. Scrapes listings from ToS-compliant job APIs, filters against fixed criteria (stipend, location, role, no PPO), tailors a resume/cover letter per posting from a live scan of your GitHub repos, and tracks application state in Postgres — with two mandatory human approval gates before anything is marked "applied." Nothing is ever auto-submitted anywhere; approving just means your materials are ready and the DB reflects that you're applying.

## Setup

```
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt
copy .env.example .env
```

Fill in `.env`:

| Variable | Where to get it |
|---|---|
| `DATABASE_URL` | A [Neon](https://neon.tech) Postgres project. Any plain `postgresql://...` connection string works — the app rewrites it to use the psycopg3 driver automatically. |
| `OPENROUTER_API_KEY` | Free signup at [openrouter.ai](https://openrouter.ai) → Settings → Keys → Create Key. Used only for resume/cover-letter generation, via free-tier models. |
| `ADZUNA_APP_ID` / `ADZUNA_APP_KEY` | Free signup at [developer.adzuna.com](https://developer.adzuna.com) — both values are shown on your dashboard immediately after signup. |
| `GITHUB_TOKEN` | A GitHub **personal access token**: [github.com/settings/tokens](https://github.com/settings/tokens) → Generate new token (classic) → check `repo` scope only if you want private repos included → copy the token (shown once). **This is per-person, not tied to this codebase** — whoever's token is in `.env` gets *their* repos scanned and ranked against each job posting, not anyone else's. No OAuth flow needed since this runs locally for one user at a time. |

Then set up your resume profile — the **static** facts only (education, past experience, hackathons, skills). Projects are *not* listed here; they're pulled live from your GitHub repos and picked per-application based on fit with each job description.

```
copy resume\base_profile.example.yaml resume\base_profile.yaml
```

Edit `resume/base_profile.yaml` with your real details (this file is gitignored — it never gets committed).

Finally, run the DB migration once:

```
alembic upgrade head
```

This also requires the `vector` extension enabled on your Postgres database (`CREATE EXTENSION IF NOT EXISTS vector;` — a one-time step if your Neon project doesn't have it yet).

## Run

```
uvicorn app.main:app --reload
```

Then check `http://127.0.0.1:8000/health`.

**Frontend** — a React dashboard is the primary way to use this day to day (Kanban board + list view, gate reviews, stats). In a second terminal:

```
cd frontend
npm install
copy .env.example .env
npm run dev
```

Opens on `http://localhost:5173`. See [`frontend/README.md`](frontend/README.md) for details.

## Using it via the API directly

The frontend covers all of this, but the API works standalone too (useful for scripting, or if you're only running the backend):

**1. Trigger a scan** — scrapes sources, ingests listings, sweeps stale applications, filters new listings, and starts the tailoring pipeline for anything that passes:

```
curl -X POST http://127.0.0.1:8000/scan
```

The response's `pending_reviews` lists anything now waiting on you.

**2. Review the auto-picked GitHub projects** (gate 1) for each pending application — the request itself is what pauses the pipeline until you respond:

```
curl -X POST http://127.0.0.1:8000/applications/{id}/project-selection \
  -H "Content-Type: application/json" \
  -d '{"action": "approve", "selected_repo_names": ["repo-a", "repo-b"]}'
```

Passing `{"action": "decline"}` instead drops the application entirely (the underlying job listing stays in the DB, so you can reconsider it in a future scan). `DELETE /applications/{id}` removes any application regardless of state.

**3. Review the tailored resume/cover letter** (gate 2) — the response from step 2 includes the full draft, with any `flagged_terms` on a bullet meaning the wording introduced something not traceable back to your actual GitHub README or profile:

```
curl -X POST http://127.0.0.1:8000/applications/{id}/final-approval \
  -H "Content-Type: application/json" \
  -d '{"action": "approve"}'
```

Approving marks the application `applied` in the DB and stores the final materials — you still submit it yourself via the listing's URL.

**4. Check on things anytime:**

```
curl http://127.0.0.1:8000/applications              # everything, newest first
curl http://127.0.0.1:8000/applications?status=pending
curl http://127.0.0.1:8000/applications/{id}          # full detail, including any pending review
curl http://127.0.0.1:8000/applications/stats         # totals, response rate, avg stipend, role-tier breakdown
```

Full API contract, including every field shape: [`BACKEND_REFERENCE.md`](BACKEND_REFERENCE.md).

## Deployment

The backend and frontend deploy independently — backend anywhere that runs a long-lived Python process (Render, Railway, Fly.io, a VPS), frontend anywhere that serves static files (Vercel, Netlify, Cloudflare Pages).

**Backend:**
- Run without `--reload`: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- Set every variable from `.env.example` in the host's environment, including `DATABASE_URL` pointed at your real Neon (or other Postgres) instance.
- **Set `ALLOWED_ORIGINS` to your deployed frontend's real URL** — it defaults to `localhost:5173` only, so requests from a deployed frontend are CORS-blocked until this is set (comma-separated if you need more than one, e.g. keeping local dev working too).
- Run `alembic upgrade head` once against the production database before first boot.
- `resume/base_profile.yaml` isn't in git (by design) — the deployed instance needs its own copy present on disk, or `/profile` will 404 until you `PUT` one via the API/frontend.

**Frontend:**
- Set `VITE_API_BASE_URL` to the deployed backend's URL at build time, then `npm run build` in `frontend/` and deploy the resulting `dist/` folder as a static site.

## Layout

- `app/db/` — SQLAlchemy models + session
- `app/nodes/scraper/` — RemoteOK (live, no key) + Adzuna (needs keys) job sources
- `app/nodes/matcher/` — hard filters (stipend/location/PPO) + embedding-based role classification
- `app/nodes/tailor/` — GitHub project fetch/ranking + LLM resume/cover-letter generation
- `app/nodes/tracker/` — listing ingest/upsert + stale-application sweep
- `app/graph/` — the LangGraph pipeline wiring it all together, with the two human-approval gates
- `app/api/` — FastAPI routes
- `app/schemas/` — Pydantic models shared across modules
- `resume/` — your structured profile (`base_profile.yaml`, gitignored — copy from `base_profile.example.yaml`)
- `alembic/` — DB migrations
- `frontend/` — React dashboard (see [`frontend/README.md`](frontend/README.md))

## Tests

```
pytest
```

Most tests are network-free (pure functions with canned inputs). `tests/test_tracker_*.py` and `tests/test_api.py` hit your real `DATABASE_URL` directly (with full setup/teardown) rather than mocking, since DB behavior is the actual thing being tested there.
