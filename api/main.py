"""
Aplicación FastAPI de ARXIA.
"""

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse

from api.routes import router


# ============================================================================
# PATHS
# ============================================================================

BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"


# ============================================================================
# APPLICATION
# ============================================================================

app = FastAPI(
    title="ARXIA API",
    description=(
        "Motor de decisión multimodelo para análisis de eventos "
        "de motorsport mediante Gemini y Ollama."
    ),
    version="1.0.0",
)


# ============================================================================
# ROUTES
# ============================================================================

app.include_router(router)


@app.get("/", include_in_schema=False)
def landing_page():
    """Sirve la landing page de ARXIA."""
    return FileResponse(FRONTEND_DIR / "index.html")


@app.get("/dashboard", include_in_schema=False)
def dashboard_page():
    """Sirve el dashboard principal de ARXIA."""
    return FileResponse(FRONTEND_DIR / "dashboard.html")