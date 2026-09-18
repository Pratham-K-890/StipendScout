import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.api.routes import applications, profile, scan, search_settings
from app.config import settings
from app.exceptions import NotConfiguredError
from app.graph.checkpointer import get_checkpointer

logger = logging.getLogger("stipendscout")


@asynccontextmanager
async def lifespan(app: FastAPI):
    with get_checkpointer() as checkpointer:
        app.state.checkpointer = checkpointer
        yield


class UnhandledExceptionMiddleware(BaseHTTPMiddleware):
    # A route-level `@app.exception_handler(Exception)` looks like the
    # obvious fix, but Starlette special-cases the bare Exception/500 key:
    # it's routed to ServerErrorMiddleware, which build_middleware_stack()
    # places OUTSIDE every app.add_middleware() layer, CORS included —
    # confirmed by reading starlette/applications.py directly, not assumed.
    # A response built there never passes through CORSMiddleware's response
    # handling, so it carries no Access-Control-Allow-Origin header and a
    # real cross-origin request sees a blocked/network error, not a
    # readable one. A genuine middleware, registered before CORSMiddleware
    # below (add_middleware prepends, so this ends up the inner of the two
    # and CORS the outer), catches the exception inside CORS's wrapping
    # instead, so its JSON response gets CORS-processed normally.
    async def dispatch(self, request: Request, call_next):
        try:
            return await call_next(request)
        except Exception:
            logger.exception("Unhandled exception on %s %s", request.method, request.url.path)
            return JSONResponse(status_code=500, content={"detail": "Internal server error"})


app = FastAPI(title="StipendScout", lifespan=lifespan)
app.add_middleware(UnhandledExceptionMiddleware)
app.add_middleware(
    CORSMiddleware,
    # ALLOWED_ORIGINS in .env — defaults to Vite's local dev port. A
    # deployed frontend on a real domain must be added there, or every
    # request gets CORS-blocked (see README's deployment section).
    allow_origins=settings.allowed_origins_list,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(scan.router)
app.include_router(applications.router)
app.include_router(profile.router)
app.include_router(search_settings.router)


@app.exception_handler(NotConfiguredError)
async def not_configured_handler(request: Request, exc: NotConfiguredError) -> JSONResponse:
    # Not caught by the middleware above: FastAPI dispatches a specific
    # exception class like this one through ExceptionMiddleware, which is
    # always innermost (closer to the route than any add_middleware layer,
    # CORS included) — so this one was never affected by the ordering issue.
    return JSONResponse(status_code=503, content={"detail": str(exc)})


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
