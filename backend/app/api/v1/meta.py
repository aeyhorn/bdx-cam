from fastapi import APIRouter

from app.core.config import get_settings

router = APIRouter(prefix="/meta", tags=["meta"])


@router.get("/version")
def meta_version() -> dict[str, str]:
    settings = get_settings()
    return {"status": "ok", "release_id": settings.RELEASE_ID}
