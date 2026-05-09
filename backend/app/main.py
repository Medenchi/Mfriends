from contextlib import asynccontextmanager

from backend.app.api import auth, chat, moderation, profiles, requests, uploads, verification
from backend.app.core.config import get_settings
from backend.app.db.init_db import init_db
from backend.app.realtime.routes import router as realtime_router
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    settings = get_settings()
    settings.upload_dir.mkdir(parents=True, exist_ok=True)
    yield


settings = get_settings()
settings.upload_dir.mkdir(parents=True, exist_ok=True)
app = FastAPI(title=settings.app_name, version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

app.include_router(auth.router, prefix="/api")
app.include_router(profiles.router, prefix="/api")
app.include_router(requests.router, prefix="/api")
app.include_router(chat.router, prefix="/api")
app.include_router(uploads.router, prefix="/api")
app.include_router(moderation.router, prefix="/api")
app.include_router(verification.router, prefix="/api")
app.include_router(realtime_router)
app.mount("/uploads", StaticFiles(directory=settings.upload_dir), name="uploads")


@app.get("/api/health")
def health():
    return {"status": "ok", "service": settings.app_name}
