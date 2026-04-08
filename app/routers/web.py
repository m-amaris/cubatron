from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter()
TEMPLATES_DIR = Path(__file__).resolve().parents[1] / "templates"


def render_template(name: str) -> HTMLResponse:
    return HTMLResponse((TEMPLATES_DIR / name).read_text(encoding="utf-8"), status_code=200)


@router.get("/", response_class=HTMLResponse)
def login_page():
    return render_template("login.html")


@router.get("/dashboard", response_class=HTMLResponse)
def dashboard_page():
    return render_template("dashboard.html")
