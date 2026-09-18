# StipendScout — Frontend

React + Vite + TypeScript dashboard for reviewing and tracking internship applications. Talks to the FastAPI backend in `../app` — see the [root README](../README.md) for backend setup and the two-gate approval workflow this UI drives.

## Setup

```
npm install
copy .env.example .env
```

`VITE_API_BASE_URL` in `.env` defaults to `http://127.0.0.1:8000` (the backend's local dev address) — only needs changing once you deploy and the backend lives somewhere else.

## Run

```
npm run dev
```

Opens on `http://localhost:5173` — this exact origin (and `127.0.0.1:5173`) is what the backend's CORS allowlist expects by default; see the root README if you change it.

## Build

```
npm run build
```

Outputs static files to `dist/` — deployable to any static host (Vercel, Netlify, Cloudflare Pages, etc.). Set `VITE_API_BASE_URL` to the deployed backend's URL at build time, and add the deployed frontend's URL to the backend's `ALLOWED_ORIGINS`.

## Stack

- React 19 + TypeScript, Vite
- Tailwind v4
- shadcn/ui components (Base UI primitives, not Radix — see `components.json`)
- TanStack Query for server state
- React Router

## Lint

```
npm run lint
```
