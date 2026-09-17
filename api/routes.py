"""
Rutas HTTP de ARXIA.
La API expone el motor de decisión multimodelo
Gemini vs Ollama.
"""
import os
from fastapi import APIRouter, HTTPException
from core.application.arxia_core import ArxiaCore
from core.application.comparison_engine import ComparisonEngine
from core.application.decision_engine import DecisionEngine
from core.application.risk_engine import RiskEngine
from core.domain.schemas import ArxiaResult, RaceEvent
from infrastructure.gemini_provider import GeminiProvider
from infrastructure.ollama_provider import OllamaProvider
from infrastructure.mocks import (
    MockGeminiProvider,
    MockOllamaProvider,
)
router = APIRouter()

# ============================================================================
# HEALTH CHECK
# ============================================================================
@router.get("/")
def health_check() -> dict[str, str]:
    """Comprueba que la API de ARXIA está disponible."""
    return {
        "application": "ARXIA",
        "status": "running",
        "architecture": "gemini_vs_ollama",
    }

# ============================================================================
# CORE FACTORY
# ============================================================================
def create_arxia_core() -> ArxiaCore:
    """
    Construye ARXIA utilizando los proveedores configurados.
    Modos disponibles:

    - mock: utiliza MockGeminiProvider y MockOllamaProvider.
    - real: utiliza GeminiProvider y OllamaProvider.

    Por defecto se utiliza mock para facilitar el desarrollo local.
    """

    provider_mode = os.getenv(
        "ARXIA_PROVIDER_MODE",
        "mock",
    ).lower()

    comparison_engine = ComparisonEngine()
    risk_engine = RiskEngine()
    decision_engine = DecisionEngine()

    if provider_mode == "mock":
        gemini_provider = MockGeminiProvider()
        ollama_provider = MockOllamaProvider()

    elif provider_mode == "real":
        gemini_provider = GeminiProvider()
        ollama_provider = OllamaProvider()

    else:
        raise ValueError(
            f"Modo de proveedores no soportado: {provider_mode}"
        )

    return ArxiaCore(
        gemini_provider=gemini_provider,
        ollama_provider=ollama_provider,
        comparison_engine=comparison_engine,
        risk_engine=risk_engine,
        decision_engine=decision_engine,
    )
# Instancia global utilizada por el endpoint /analyze.
arxia_core = create_arxia_core()

# ============================================================================
# ARXIA ENDPOINT
# ============================================================================
@router.post(
    "/analyze",
    response_model=ArxiaResult,
)
def analyze_race_event(
    race_event: RaceEvent,
) -> ArxiaResult:
    """
    Recibe un evento de motorsport y ejecuta el pipeline completo de ARXIA.
    Flujo:

    1. Gemini analiza el evento.
    2. Ollama analiza el evento.
    3. ComparisonEngine compara ambos análisis.
    4. RiskEngine evalúa el riesgo.
    5. DecisionEngine genera la decisión.
    6. ARXIA devuelve el resultado completo.
    """

    try:
        return arxia_core.process(race_event)

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Error procesando el evento con ARXIA: {exc}",
        ) from exc