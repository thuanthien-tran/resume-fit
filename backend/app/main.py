from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api import admin, auth, health, jobs, uploads
from app.api.dependencies import get_current_user
from app.core.config import settings
from app.core.logging import setup_logging

setup_logging()

app = FastAPI(title="AI Resume Matching Platform", version="0.1.0")

def _cors_origins() -> list[str]:
    configured = [origin.strip() for origin in settings.cors_origins.split(",") if origin.strip()]
    if configured:
        return configured
    if settings.app_env.lower() in {"local", "dev", "development"}:
        return ["*"]
    return []


app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins(),
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


app.include_router(health.router, prefix="/api")
app.include_router(auth.router, prefix="/api")
app.include_router(uploads.router, prefix="/api")
app.include_router(jobs.router, prefix="/api")
app.include_router(admin.router, prefix="/api")


@app.get("/api/me")
def get_me(current_user=Depends(get_current_user)):
    return {
        "id": str(current_user.id),
        "email": current_user.email,
        "full_name": current_user.full_name,
        "role": current_user.role,
        "status": current_user.status,
    }
