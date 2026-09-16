import pytest

from core.application.arxia_core import ArxiaCore
from core.application.comparison_engine import ComparisonEngine
from core.application.decision_engine import DecisionEngine
from core.application.risk_engine import RiskEngine
from core.domain.enums import (
    AnalysisCategory,
    AnalysisStatus,
    AnalysisUrgency,
    ComparisonStatus,
    DecisionType,
    EventType,
    Provider,
    RecommendationAction,
    ReviewStatus,
    RiskLevel,
    RaceSession,
    TyreCompound,
)
from core.domain.schemas import (
    AIAnalysis,
    ModelMetrics,
    RaceEvent,
    Recommendation,
)
from infrastructure.mocks import (
    MockGeminiProvider,
    MockOllamaProvider,
)


# ============================================================================
# HELPERS
# ============================================================================


def build_metrics() -> ModelMetrics:
    """Construye métricas válidas para los análisis de prueba."""

    return ModelMetrics(
        input_tokens=100,
        output_tokens=50,
        total_tokens=150,
        latency_ms=100.0,
        cost=0.0,
        retries=0,
    )


def build_recommendation(
    *,
    action: RecommendationAction = RecommendationAction.PIT_STOP,
    target_lap: int | None = 20,
    tyre_compound: TyreCompound | None = TyreCompound.MEDIUM,
    confidence: float = 0.90,
) -> Recommendation:
    """Construye una recomendación estratégica válida para las pruebas."""

    return Recommendation(
        action=action,
        target_lap=target_lap,
        tyre_compound=tyre_compound,
        confidence=confidence,
        rationale="Strategic recommendation for the current race situation.",
    )


def build_analysis(
    *,
    provider: Provider,
    status: AnalysisStatus = AnalysisStatus.SUCCESS,
    confidence: float = 0.90,
    error: str | None = None,
) -> AIAnalysis:
    """Construye un análisis válido para las pruebas del orquestador."""

    return AIAnalysis(
        provider=provider,
        model="test-model",
        status=status,
        category=AnalysisCategory.RACE_STRATEGY,
        urgency=AnalysisUrgency.MEDIUM,
        confidence=confidence,
        summary="Strategic race analysis for the current situation.",
        reasoning="Strategic reasoning for the current race event.",
        recommendation=build_recommendation(
            confidence=confidence,
        ),
        metrics=build_metrics(),
        error=error,
    )


def build_event() -> RaceEvent:
    """Construye un evento de carrera válido para las pruebas."""

    return RaceEvent(
        circuit="Monza",
        session=RaceSession.RACE,
        lap=20,
        driver="Driver",
        team="Team",
        position=5,
        event_type=EventType.STRATEGIC_OPPORTUNITY,
        description="Strategic race event.",
    )


def build_core(
    *,
    gemini_provider=None,
    ollama_provider=None,
) -> ArxiaCore:
    """Construye ArxiaCore con sus dependencias de aplicación."""

    return ArxiaCore(
        gemini_provider=(
            gemini_provider
            if gemini_provider is not None
            else MockGeminiProvider()
        ),
        ollama_provider=(
            ollama_provider
            if ollama_provider is not None
            else MockOllamaProvider()
        ),
        comparison_engine=ComparisonEngine(),
        risk_engine=RiskEngine(),
        decision_engine=DecisionEngine(),
    )


# ============================================================================
# INITIALIZATION
# ============================================================================


def test_arxia_core_initializes_with_dependencies():
    """Comprueba que ArxiaCore acepta correctamente sus dependencias."""

    core = build_core()

    assert isinstance(core.comparison_engine, ComparisonEngine)
    assert isinstance(core.risk_engine, RiskEngine)
    assert isinstance(core.decision_engine, DecisionEngine)


# ============================================================================
# COMPLETE PIPELINE
# ============================================================================


def test_process_builds_complete_arxia_result():
    """Comprueba que process ejecuta y devuelve el pipeline completo."""

    core = build_core()

    result = core.process(build_event())

    assert result.race_event.circuit == "Monza"

    assert result.gemini_analysis.provider == Provider.GEMINI
    assert result.gemini_analysis.status == AnalysisStatus.SUCCESS

    assert result.ollama_analysis.provider == Provider.OLLAMA
    assert result.ollama_analysis.status == AnalysisStatus.SUCCESS

    assert result.comparison.status == ComparisonStatus.COMPLETED

    assert result.risk_assessment.risk_level == RiskLevel.LOW
    assert result.risk_assessment.risk_score == 0

    assert result.decision.decision == DecisionType.AUTOMATIC
    assert result.decision.reason.value == "models_agree"

    assert result.human_review is None


def test_process_preserves_race_event():
    """Comprueba que el evento original se conserva en el resultado."""

    core = build_core()
    event = build_event()

    result = core.process(event)

    assert result.race_event == event
    assert result.race_event.id == event.id


# ============================================================================
# PROVIDER FAILURE
# ============================================================================


class FailingGeminiProvider:
    """Simula un fallo del proveedor Gemini durante el pipeline."""

    def analyze(self, race_event: RaceEvent) -> AIAnalysis:
        """Devuelve un análisis fallido de Gemini."""

        return build_analysis(
            provider=Provider.GEMINI,
            status=AnalysisStatus.ERROR,
            confidence=0.0,
            error="Gemini provider failed.",
        )


def test_provider_failure_requires_human_review():
    """Comprueba que un fallo de proveedor termina en revisión humana."""

    core = build_core(
        gemini_provider=FailingGeminiProvider(),
    )

    result = core.process(build_event())

    assert result.gemini_analysis.status == AnalysisStatus.ERROR
    assert result.ollama_analysis.status == AnalysisStatus.SUCCESS

    assert result.comparison.status == ComparisonStatus.INSUFFICIENT_DATA

    assert result.decision.decision == DecisionType.HUMAN_REVIEW
    assert result.decision.risk_level == RiskLevel.HIGH

    assert result.human_review is not None
    assert result.human_review.status == ReviewStatus.PENDING
    assert result.human_review.final_decision is None
    assert result.human_review.reviewed_at is None


# ============================================================================
# HUMAN REVIEW
# ============================================================================


class DisagreeingOllamaProvider:
    """Simula un proveedor Ollama que propone otra acción estratégica."""

    def analyze(self, race_event: RaceEvent) -> AIAnalysis:
        """Devuelve un análisis válido con una acción diferente."""

        return build_analysis(
            provider=Provider.OLLAMA,
        ).model_copy(
            update={
                "recommendation": build_recommendation(
                    action=RecommendationAction.STAY_OUT,
                    target_lap=20,
                    tyre_compound=TyreCompound.MEDIUM,
                    confidence=0.90,
                )
            },
        )


def test_model_disagreement_creates_pending_human_review():
    """Comprueba que el desacuerdo entre modelos crea revisión humana."""

    core = build_core(
        ollama_provider=DisagreeingOllamaProvider(),
    )

    result = core.process(build_event())

    assert result.comparison.status == ComparisonStatus.COMPLETED
    assert result.comparison.strategic_agreement.value == "disagree"

    assert result.decision.decision == DecisionType.HUMAN_REVIEW
    assert result.human_review is not None
    assert result.human_review.status == ReviewStatus.PENDING


# ============================================================================
# DEPENDENCY ORCHESTRATION
# ============================================================================


class TrackingProvider:
    """Proveedor de prueba que registra si recibió el RaceEvent."""

    def __init__(
        self,
        provider: Provider,
    ):
        self.provider = provider
        self.received_event = None

    def analyze(self, race_event: RaceEvent) -> AIAnalysis:
        """Registra el evento recibido y devuelve un análisis válido."""

        self.received_event = race_event

        return build_analysis(
            provider=self.provider,
        )


def test_process_passes_same_event_to_both_providers():
    """Comprueba que ambos proveedores reciben el mismo evento."""

    gemini = TrackingProvider(Provider.GEMINI)
    ollama = TrackingProvider(Provider.OLLAMA)

    core = build_core(
        gemini_provider=gemini,
        ollama_provider=ollama,
    )

    event = build_event()

    core.process(event)

    assert gemini.received_event is event
    assert ollama.received_event is event


# ============================================================================
# RESULT STRUCTURE
# ============================================================================


def test_process_returns_all_pipeline_components():
    """Comprueba que el resultado contiene todos los componentes del pipeline."""

    core = build_core()

    result = core.process(build_event())

    assert result.race_event is not None
    assert result.gemini_analysis is not None
    assert result.ollama_analysis is not None
    assert result.comparison is not None
    assert result.risk_assessment is not None
    assert result.decision is not None
    assert result.processed_at is not None


# ============================================================================
# INVALID PROVIDER OUTPUT
# ============================================================================


class InvalidGeminiProvider:
    """Simula un proveedor que devuelve un análisis de otro proveedor."""

    def analyze(self, race_event: RaceEvent) -> AIAnalysis:
        """Devuelve deliberadamente un análisis con provider incorrecto."""

        return build_analysis(
            provider=Provider.OLLAMA,
        )


def test_invalid_provider_output_fails_result_validation():
    """Comprueba que un análisis de proveedor incorrecto no pasa el dominio."""

    core = build_core(
        gemini_provider=InvalidGeminiProvider(),
    )

    with pytest.raises(ValueError):
        core.process(build_event())