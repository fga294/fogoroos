"""
U-14 stats FastAPI application.

Run from repo root:
  cd backend && uvicorn app.main:app --host 127.0.0.1 --port 8000

Or with env:
  DATABASE_URL=mysql+pymysql://... ADMIN_PASSWORD=... uvicorn app.main:app --host 127.0.0.1 --port 8000
"""

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .routers import events, fitness, matches, players, stats

app = FastAPI(
    title="U-14 Team Stats API",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    _request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors(), "message": "Validation failed"},
    )


# Broad CORS for local dev; behind Nginx same-origin, browsers send same-origin only.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health", tags=["health"])
def health_check() -> dict[str, str]:
    """Lightweight probe for monitoring and deploy scripts."""
    return {"status": "ok"}


app.include_router(players.router, prefix="/api")
app.include_router(matches.router, prefix="/api")
app.include_router(events.router, prefix="/api")
app.include_router(fitness.router, prefix="/api")
app.include_router(stats.router, prefix="/api")
