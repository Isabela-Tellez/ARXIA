"""
Aplicación FastAPI de ARXIA.
"""

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from api.routes import router


# ============================================================================
# PATHS
# ============================================================================

BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"

app = FastAPI()

# Debajo de app = FastAPI(...) y antes de las rutas
app.mount("/assets", StaticFiles(directory=BASE_DIR / "assets"), name="assets")

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

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# STATIC FILES
# ============================================================================

app.mount("/css", StaticFiles(directory=FRONTEND_DIR / "css"), name="css")
app.mount("/js", StaticFiles(directory=FRONTEND_DIR / "js"), name="js")

app.mount("/assets", StaticFiles(directory=BASE_DIR / "assets"), name="assets")


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