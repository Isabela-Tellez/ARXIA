"""
Mock Providers utilizados durante el desarrollo de ARXIA.

Simulan las respuestas de Gemini y Ollama sin depender todavía
de APIs externas.
"""

from core.domain.enums import (
    AnalysisCategory,
    AnalysisStatus,
    AnalysisUrgency,
    Provider,
    RecommendationAction,
    TyreCompound,
)
from core.domain.schemas import (
    AIAnalysis,
    ModelMetrics,
    RaceEvent,
    Recommendation,
)


# ============================================================================
# HELPERS
# ============================================================================


def _build_metrics() -> ModelMetrics:
    """Genera métricas ficticias para los modelos mock."""

    return ModelMetrics(
        input_tokens=100,
        output_tokens=50,
        total_tokens=150,
        latency_ms=100.0,
        cost=0.0,
        retries=0,
    )


def _build_recommendation(
    *,
    action: RecommendationAction = RecommendationAction.PIT_STOP,
    target_lap: int = 20,
    tyre_compound: TyreCompound = TyreCompound.MEDIUM,
    confidence: float = 0.92,
) -> Recommendation:
    """Construye una recomendación estratégica mock válida."""

    return Recommendation(
        action=action,
        target_lap=target_lap,
        tyre_compound=tyre_compound,
        confidence=confidence,
        rationale=(
            "Pit stop recomendado para aprovechar la ventana "
            "estratégica y mantener el ritmo competitivo."
        ),
    )


def _build_analysis(
    *,
    provider: Provider,
    model: str,
    confidence: float,
) -> AIAnalysis:
    """Construye un análisis mock válido."""

    return AIAnalysis(
        provider=provider,
        model=model,
        status=AnalysisStatus.SUCCESS,
        category=AnalysisCategory.RACE_STRATEGY,
        urgency=AnalysisUrgency.MEDIUM,
        confidence=confidence,
        summary=(
            "Análisis estratégico simulado para la situación "
            "actual de carrera."
        ),
        reasoning=(
            "El modelo identifica una ventana estratégica favorable "
            "para realizar una parada en boxes."
        ),
        recommendation=_build_recommendation(),
        metrics=_build_metrics(),
        error=None,
    )


# ============================================================================
# GEMINI MOCK
# ============================================================================


class MockGeminiProvider:
    """Simula el proveedor Gemini de ARXIA."""

    def analyze(self, race_event: RaceEvent) -> AIAnalysis:
        """Devuelve un análisis estratégico simulado."""

        return _build_analysis(
            provider=Provider.GEMINI,
            model="mock-gemini",
            confidence=0.95,
        )


# ============================================================================
# OLLAMA MOCK
# ============================================================================


class MockOllamaProvider:
    """Simula el proveedor Ollama de ARXIA."""

    def analyze(self, race_event: RaceEvent) -> AIAnalysis:
        """Devuelve un análisis estratégico simulado."""

        return _build_analysis(
            provider=Provider.OLLAMA,
            model="mock-ollama",
            confidence=0.92,
        )