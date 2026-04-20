import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import get_settings
from app.db.session import SessionLocal
from app.services.system_build_service import parse_build_specs, register_startup_builds

settings = get_settings()

app = FastAPI(title=settings.PROJECT_NAME, version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_list(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1_PREFIX)

Path(settings.UPLOAD_DIR).mkdir(parents=True, exist_ok=True)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.on_event("startup")
def startup() -> None:
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    if not settings.SYSTEM_BUILD_AUTOINCREMENT_ON_STARTUP:
        return
    db = SessionLocal()
    try:
        specs = parse_build_specs(settings.SYSTEM_BUILD_STARTUP_SPECS)
        if specs:
            register_startup_builds(db, specs, force_increment=settings.SYSTEM_BUILD_FORCE_INCREMENT)
            db.commit()
    except Exception:
        db.rollback()
    finally:
        db.close()
