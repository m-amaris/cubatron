from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import FileResponse

router = APIRouter()
BASE_DIR = Path(__file__).resolve().parents[1]
SPA_INDEX = BASE_DIR / "static" / "index.html"


def _spa_response() -> FileResponse:
    # Return built SPA index. Assumes frontend build outputs into app/static
    return FileResponse(str(SPA_INDEX))


@router.get("/")
def root():
    return _spa_response()


@router.get("/dashboard")
def dashboard():
    return _spa_response()


@router.get("/{full_path:path}")
def spa_catchall(full_path: str):
    # Keep API and static routes handled by their routers/mounts; this
    # catch-all will be reached for other paths and should serve the SPA.
    return _spa_response()
