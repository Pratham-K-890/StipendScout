# StipendScout Backend Reference

Complete API contract for the FastAPI backend, for designing a frontend against. Base URL in dev: `http://127.0.0.1:8000`. CORS currently allowlists only `http://localhost:5173` and `http://127.0.0.1:5173` (see `app/main.py` — change this if building a frontend on a different port/origin).

## What this app does

An autonomous internship-application pipeline: scrapes internship listings (Adzuna), filters them against fixed criteria (stipend ≥ ₹10k/month, Bengaluru-or-remote, role priority backend > ML/DS > AI-agent, no PPO), then for each listing that passes, ranks the candidate's own GitHub repos by fit and uses an LLM to draft a tailored resume + cover letter — with **two mandatory human-approval checkpoints** before anything is considered "applied." Nothing is ever auto-submitted anywhere external; approving just means the materials are finalized and the record is marked applied.

## The core state machine (read this before designing screens)

Each `Application` row moves through a LangGraph pipeline with two pause points (implemented via `interrupt()`), *not* a simple linear flow:

```
[Listing scraped] → matcher filters → (fails → no Application row created, nothing to show)
                                     → (passes → Application row created, status="pending")
                                          ↓
                                    rank GitHub projects
                                          ↓
                        ⏸ GATE 1: "project_selection" — waiting on you
                          (POST .../project-selection to resume)
                          action="decline" → Application row DELETED, nothing left
                          action="approve" → proceeds to tailor step (~15-20s real LLM call)
                                          ↓
                        ⏸ GATE 2: "final_approval" — waiting on you
                          (POST .../final-approval to resume)
                          action="decline" → Application row DELETED
                          action="approve" → status="applied", applied_at set, DONE
                                          ↓
                [Outside this system entirely: interview / rejected via PATCH .../status]
```

**Key implication for UI design:** an `Application` at any moment is in exactly one of these states, and `GET /applications/{id}` tells you which via the `pending_review` field:
- `pending_review.type === "project_selection"` → show the ranked-projects picker
- `pending_review.type === "final_approval"` → show the generated resume/cover-letter for approval
- `pending_review === null` and `tailored_resume !== null` → fully resolved (applied/interview/rejected/stale), show read-only
- `pending_review === null` and `tailored_resume === null` → shouldn't normally happen (would mean matcher passed but graph never ran)

Both approve actions cost real wall-clock time (an actual LLM call), roughly 15-20 seconds for gate 1→tailoring, near-instant for gate 2 (no LLM call there, just a DB write). Design for a loading state on gate 1's approve button specifically.

Declining at *either* gate **deletes the Application row entirely** (not a soft "declined" status — there is no such status). The underlying `Listing` is untouched and will be picked up again on a future scan if you change your mind.

---

## Endpoints

### `GET /health`
No auth, no params. Returns `{"status": "ok"}`. Liveness check only.

### `POST /scan`
Triggers the full pipeline: scrape all enabled sources → ingest into DB → sweep stale applications → for every listing without an existing Application, run the matcher, and for passers, kick off the graph up to its first interrupt.

No request body. Can take a while (multiple Adzuna API calls per configured search query, plus a GitHub fetch + LLM summary call per newly-passing listing) — design for a loading/spinner state, this isn't instant.

**Response** (`ScanSummary`):
```jsonc
{
  "sources_scraped": ["remoteok", "adzuna"],
  "new_applications_started": 2,
  "pending_reviews": [
    {
      "application_id": "uuid",
      "review_type": "project_selection",
      "payload": { /* same shape as pending_review below */ }
    }
  ]
}
```
`pending_reviews` is a convenience — it's *also* discoverable by listing applications and fetching each detail; the scan response just saves you round-trips for what got created in that specific run.

### `GET /applications?status={status}`
List all applications, newest first. `status` query param is optional; one of `pending | applied | rejected | interview | stale`. Invalid value → `400`.

**Response**: array of `ApplicationSummary`:
```jsonc
{
  "id": "uuid",
  "status": "pending",                 // pending | applied | rejected | interview | stale
  "listing_title": "Machine Learning Intern",
  "listing_company": "FRND",
  "listing_url": "https://www.adzuna.in/...",   // the ORIGINAL job posting, not this app
  "created_at": "2026-09-11T06:24:48.355098+00:00",   // ISO 8601
  "status_changed_at": "2026-09-11T06:26:17.594855+00:00",
  "applied_at": "2026-09-11T06:26:03.785001+00:00"     // null until status becomes "applied"
}
```

### `GET /applications/{id}`
Full detail for one application. `404` if the id is malformed (not a valid UUID) or doesn't exist.

**Response** (`ApplicationDetail` — extends `ApplicationSummary` with):
```jsonc
{
  // ...all ApplicationSummary fields, plus:
  "jd_snapshot": {                     // frozen JD facts captured when this Application was created
    "title": "...", "company": "...", "description": "...", "url": "..."
  },
  "listing_summary": {                 // JDSummary — see schema below. null if somehow not computed.
    "stipend_amount": 20000,
    "stipend_status": "confirmed_ok",  // confirmed_ok | confirmed_below_minimum | unknown
    "location": "Bangalore, Karnataka",
    "is_remote": false,
    "ppo_detected": false,
    "role_tier": "ml_data_science",    // backend | ml_data_science | ai_agent_llm | null
    "responsibilities": ["..."],       // AI-extracted, empty list if JD didn't state any
    "requirements": ["..."],
    "duration": "6 month",             // or null
    "benefits": ["..."]
  },
  "tailored_resume": { /* TailoredResume, see below */ } | null,
  "tailored_cover_letter": "Dear Hiring Team...\n\n..." | null,   // plain text, real newlines
  "pending_review": { /* see "pending_review payload shapes" below */ } | null
}
```

### `GET /applications/{id}/resume.pdf`
Returns the tailored resume rendered as a PDF (`application/pdf`, `Content-Disposition: inline`). `404` if the application doesn't exist or has no `tailored_resume` yet (i.e. hasn't reached gate 2). This is a plain file-download link target — no JSON, don't fetch it with your JSON client. Rendered fresh from the stored structured resume on every request — never cached — so a rendering-side code change (layout, spacing) applies retroactively to old applications too; a *content*-side change (e.g. which skills get selected) does not, since that's baked into the stored data at gate-1-approval time.

### `DELETE /applications/{id}`
Deletes an application in any state — not just the pending-review-only decline. `204` on success, `404` if it doesn't exist. Also clears the LangGraph checkpoint thread server-side, so nothing orphaned is left behind. No confirmation step server-side — the frontend must confirm before calling this, same as decline.

### `PATCH /applications/{id}/status`
Manual override for states the automated flow can't produce itself — recording an interview call or an employer rejection, which happen outside this system.

**Request**: `{"status": "interview"}` — any of `pending | applied | rejected | interview | stale`. Invalid enum value → `422` (Pydantic validation, not a custom 400).

**Response**: updated `ApplicationSummary`. `404` if application doesn't exist.

### `POST /applications/{id}/project-selection`
Resumes a paused graph at gate 1. **400 if there's no pending `project_selection` review for this id** (wrong state — already resolved, or it's actually sitting at gate 2, or it doesn't exist).

**Request** (`ProjectSelectionRequest`):
```jsonc
{ "action": "approve", "selected_repo_names": ["repo-a", "repo-b"] }   // or "decline", then selected_repo_names is ignored
```

**Response** (on success):
```jsonc
{ "application_id": "uuid", "next_review": { /* pending_review shape, or null if declined */ } | null }
```
On `approve`: `next_review` will be the `final_approval` payload (after the ~15-20s LLM wait). On `decline`: the Application row is deleted server-side; `next_review` is `null`; a subsequent `GET /applications/{id}` will `404`.

**422** if `resume/base_profile.yaml` doesn't exist yet (tailoring needs it) — message tells the user to visit `/profile` first. Check profile existence before offering the approve action if you want to avoid this entirely (`GET /profile` returning `404` means "not set up").

### `POST /applications/{id}/final-approval`
Resumes a paused graph at gate 2. Same 400-if-wrong-state behavior as gate 1.

**Request** (`FinalApprovalRequest`): `{"action": "approve"}` or `{"action": "decline"}`.

**Response**: `{"application_id": "uuid", "next_review": null}` — always `null` on success, since there's no gate 3. On `approve`, the Application's `status` becomes `"applied"` server-side (check via a fresh `GET`). On `decline`, the row is deleted.

### `GET /profile`
Returns the candidate's static resume profile (name, education, past experience, hackathons, responsibilities, skills — **not projects**, those come from GitHub live). **404 with `{"detail": "No profile set up yet"}` if `resume/base_profile.yaml` doesn't exist** — this is the expected/normal state for a fresh clone, not an error condition to alarm the user over.

**Response** (`BaseProfile`):
```jsonc
{
  "name": "Pratham K",
  "email": "kpratham883@gmail.com",
  "phone": "+91-7676070856" | null,
  "location": "Bengaluru, India" | null,
  "links": { "linkedin": "..." | null, "github": "..." | null, "leetcode": "..." | null, "portfolio": "..." | null },
  "education": [
    { "institution": "...", "degree": "...", "branch": "..." | null, "start_year": 2024 | null, "end_year": 2028 | null, "cgpa": "9.30" | null }
  ],
  "experience": [
    { "title": "...", "company": "...", "start_date": "2026-01", "end_date": "2026-07" | null, "bullets": ["...", "..."] }
  ],
  "hackathons": [
    { "title": "...", "event": "...", "team_project": true, "bullets": ["..."] }
  ],
  "responsibilities": [
    { "title": "...", "organization": "...", "bullets": ["..."] }
  ],
  "skills": { "Languages": ["Python", "..."], "Frameworks & Libraries": ["FastAPI", "..."] }   // category name -> skills; ~50 items total realistically across ~7 categories — design the editor for that volume, not a flat list
}
```

### `PUT /profile`
Full replace — send the *entire* `BaseProfile` object back (there's no partial-patch semantics). Writes straight through to `resume/base_profile.yaml`. Returns the saved profile. No validation beyond Pydantic's type checking (e.g. no "at least one education entry" rule) — empty lists are fine.

### `GET /search-settings`
Returns what gets searched on Adzuna. **Never 404s** — if `config/search_settings.yaml` doesn't exist, returns sensible built-in defaults (unlike `/profile`, this doesn't require setup to function).

**Response** (`SearchSettings`):
```jsonc
{
  "search_queries": ["backend developer intern", "python developer intern", "machine learning intern", "data science intern", "AI agent intern"],
  "exclude_keywords": []   // listings matching any of these (title or description) are dropped before the matcher ever sees them
}
```

### `PUT /search-settings`
Full replace, same pattern as profile. Writes to `config/search_settings.yaml`.

---

## `pending_review` payload shapes

This is the field you branch your UI on. Present on `GET /applications/{id}` (`pending_review`) and on the `next_review` field returned by both resume-gate POST endpoints. `null` when nothing is currently awaiting review for that application.

### `type: "project_selection"`
```jsonc
{
  "type": "project_selection",
  "application_id": "uuid",
  "ranked_projects": [
    {
      "project": {
        "repo_name": "ai-api-assistant",
        "description": null,                 // often null — most GitHub repos here have no description field set
        "readme_excerpt": "# AI Assistant API\n\nA production-ready...",   // raw markdown, up to ~1500 chars, use as fallback when description is null
        "topics": [],
        "language": "Python" | null,
        "url": "https://github.com/user/ai-api-assistant" | null,   // null if the repo is private — don't render a dead link
        "deployed_url": "https://ai-api-assistant-production.up.railway.app" | null,  // live demo link, extracted from README if stated
        "is_private": false,
        "is_fork": false,
        "stars": 0,
        "updated_at": "2026-07-23T06:03:23Z"
      },
      "similarity": 0.6358937046116327     // 0-1 cosine similarity to the JD, sort key is already applied (list arrives pre-sorted descending)
    }
    // ...usually 5 entries (top_n default), fewer if the account has fewer eligible repos
  ]
}
```
The frontend is expected to let the user check/uncheck which `repo_name`s to send back as `selected_repo_names` — the existing frontend defaults to the top 3 pre-checked. At least one selection is required for a meaningful resume (the backend doesn't enforce a minimum, but zero selected produces an empty-handed tailoring pass).

### `type: "final_approval"`
```jsonc
{
  "type": "final_approval",
  "application_id": "uuid",
  "tailored_resume": { /* TailoredResume, identical shape to GET /applications/{id}'s tailored_resume field */ },
  "cover_letter": { "body": "Dear Hiring Team...\n\n...", "flagged_terms": [] }
}
```

## `TailoredResume` shape (appears both in `pending_review.tailored_resume` and `GET /applications/{id}.tailored_resume`)

```jsonc
{
  "name": "Pratham K",
  "email": "kpratham883@gmail.com",
  "phone": "..." | null,
  "location": "..." | null,
  "links": { "linkedin": "..." | null, "github": "..." | null, "leetcode": "..." | null, "portfolio": "..." | null },
  "education_summary": ["B.E. in Artificial Intelligence and Machine Learning, Dayananda Sagar College Of Engineering (2024-2028), CGPA 9.30"],  // pre-formatted single strings, not structured
  "highlighted_skills": { "Languages": ["Python"], "Frameworks & Libraries": ["FastAPI", "..."] },   // category name -> JD-relevant skills in that category, both orders meaningful (render order); an application tailored before this was categorized may still carry the old flat-list shape in the raw DB column, but every API response normalizes it to this shape before you ever see it
  "bullets": [
    {
      "text": "Built a production-ready AI chat API with FastAPI, Groq...",
      "source_type": "project",          // "project" | "experience" | "hackathon" | "responsibility"
      "source_ref": "ai-api-assistant",  // repo_name for projects, "Title at Company" for experience, etc. — use to group bullets by section
      "source_excerpt": "...",           // the original source text this bullet was derived from (for your own auditing UI, not usually shown to end users)
      "flagged_terms": []                // non-empty = the LLM used a term not traceable back to source_excerpt/skills — SHOW THIS, it's the anti-fabrication signal the whole approval gate exists for
    }
  ]
}
```
Group `bullets` by `source_type` for section headings (Projects / Experience / Hackathons / Responsibilities) — there's no separate "sections" field, you derive it client-side. `flagged_terms` being non-empty on any bullet or on the cover letter is the single most important thing to surface prominently before the user approves — it means the AI wrote something not traceably grounded in real source material.

---

## Error conventions

- `404` — resource not found, or a malformed UUID in the path (treated the same, so you can't distinguish "bad ID format" from "valid ID, doesn't exist" from the status code alone — the `detail` message is always `"Application not found"` either way).
- `400` — wrong-state request (e.g. approving a gate that isn't currently pending), or an invalid `status` filter value.
- `422` — Pydantic body validation failure (bad enum value, missing required field), *or* the specific "profile not set up" case on gate-1 approval.
- `503` — a required integration isn't configured (missing `GITHUB_TOKEN`/`ADZUNA_APP_ID`/etc. in `.env`) — `detail` names exactly which env var and where to set it.
- `500` — genuinely unexpected server-side failure (a dead DB connection, an LLM call that exhausted every fallback). `detail` is a generic `"Internal server error"` on purpose — the real cause goes to the server log, not the client, so don't try to branch UI behavior on this message's content.
- **Every error response, including unhandled 500s, is `{"detail": "human-readable message"}`** — this is enforced server-side by a global handler (`app/main.py`), not just a convention every route happens to follow, so build one shared error handler off this shape with confidence.

## Things a frontend needs to handle that aren't obvious from the schema alone

1. **Real latency on gate-1 approve** (~15-20s) — it's a synchronous LLM call, the HTTP request just hangs until it's done. No polling/websocket, no progress events.
2. **`GET /profile` 404 is a normal, expected state**, not an error to show scary UI for — it just means first-run setup hasn't happened.
3. **Declining deletes data.** Any UI offering "decline" should confirm first — there is no undo, though the source `Listing` does persist and can resurface on a future scan.
4. **`stipend_amount`/`stipend_status`**: absence of a confirmed stipend (`"unknown"`) does *not* mean unpaid — Adzuna truncates JDs to 500 characters server-side, so most listings simply don't have stipend text in the fetched excerpt. Don't render "unknown" as if it were a red flag.
5. **The PDF endpoint is a plain URL**, not a JSON-returning endpoint — use it as an `<a href>`/download target, not via your fetch wrapper.
6. **CORS is currently hardcoded** to `localhost:5173`/`127.0.0.1:5173` in `app/main.py` — a frontend on a different origin/port needs that list updated.
