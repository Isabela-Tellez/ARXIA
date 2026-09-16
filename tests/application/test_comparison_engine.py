import pytest

from core.application.comparison_engine import ComparisonEngine

from core.domain.enums import (
    AgreementLevel,
    AnalysisCategory,
    AnalysisStatus,
    AnalysisUrgency,
    ComparisonStatus,
    Provider,
    RecommendationAction,
    TyreCompound,
)

from core.domain.schemas import (
    AIAnalysis,
    Comparison,
    ModelMetrics,
    Recommendation,
)


# ============================================================================
# HELPERS
# ============================================================================


def build_metrics() -> ModelMetrics:
    """Construye métricas válidas para un análisis de prueba."""

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
    action: RecommendationAction = RecommendationAction.PIT_STOP,
    target_lap: int | None = 20,
    tyre_compound: TyreCompound | None = TyreCompound.MEDIUM,
) -> AIAnalysis:
    """Construye un análisis completo y válido para las pruebas."""

    return AIAnalysis(
        provider=provider,
        model="test-model",
        status=status,
        category=AnalysisCategory.RACE_STRATEGY,
        urgency=AnalysisUrgency.MEDIUM,
        confidence=confidence,
        summary="Strategic race analysis for the current situation.",
        reasoning="Strategic reasoning for the current race context.",
        recommendation=build_recommendation(
            action=action,
            target_lap=target_lap,
            tyre_compound=tyre_compound,
            confidence=confidence,
        ),
        metrics=build_metrics(),
        error=(
            "Provider failed."
            if status != AnalysisStatus.SUCCESS
            else None
        ),
    )


def build_engine() -> ComparisonEngine:
    """Construye una instancia del motor de comparación."""

    return ComparisonEngine()


# ============================================================================
# INSUFFICIENT DATA
# ============================================================================


def test_failed_analysis_produces_insufficient_data():
    """Devuelve insuficientes datos cuando un análisis no es exitoso."""

    engine = build_engine()

    gemini = build_analysis(
        provider=Provider.GEMINI,
        status=AnalysisStatus.ERROR,
    )

    ollama = build_analysis(
        provider=Provider.OLLAMA,
    )

    result = engine.compare(
        gemini_analysis=gemini,
        ollama_analysis=ollama,
    )

    assert result.status == ComparisonStatus.INSUFFICIENT_DATA
    assert result.fields == []
    assert result.strategic_agreement is None


def test_invalid_provider_produces_insufficient_data():
    """No compara análisis cuando los providers no son los esperados."""

    engine = build_engine()

    gemini = build_analysis(
        provider=Provider.OLLAMA,
    )

    ollama = build_analysis(
        provider=Provider.OLLAMA,
    )

    result = engine.compare(
        gemini_analysis=gemini,
        ollama_analysis=ollama,
    )

    assert result.status == ComparisonStatus.INSUFFICIENT_DATA


# ============================================================================
# COMPLETED COMPARISON
# ============================================================================


def test_matching_analyses_produce_completed_comparison():
    """Genera una comparación completada cuando ambos análisis son válidos."""

    engine = build_engine()

    gemini = build_analysis(
        provider=Provider.GEMINI,
    )

    ollama = build_analysis(
        provider=Provider.OLLAMA,
    )

    result = engine.compare(
        gemini_analysis=gemini,
        ollama_analysis=ollama,
    )

    assert result.status == ComparisonStatus.COMPLETED
    assert result.strategic_agreement == AgreementLevel.AGREE
    assert result.confidence_difference == 0.0
    assert result.target_lap_difference == 0


# ============================================================================
# FIELD COMPARISON
# ============================================================================


def test_category_agreement_is_detected():
    """Detecta acuerdo cuando ambos modelos usan la misma categoría."""

    engine = build_engine()

    gemini = build_analysis(
        provider=Provider.GEMINI,
    )

    ollama = build_analysis(
        provider=Provider.OLLAMA,
    )

    result = engine.compare(
        gemini_analysis=gemini,
        ollama_analysis=ollama,
    )

    field = next(
        field
        for field in result.fields
        if field.field.value == "category"
    )

    assert field.gemini_value == "race_strategy"
    assert field.ollama_value == "race_strategy"
    assert field.agreement == AgreementLevel.AGREE


def test_action_disagreement_is_detected():
    """Detecta desacuerdo cuando los modelos recomiendan acciones diferentes."""

    engine = build_engine()

    gemini = build_analysis(
        provider=Provider.GEMINI,
        action=RecommendationAction.PIT_STOP,
    )

    ollama = build_analysis(
        provider=Provider.OLLAMA,
        action=RecommendationAction.STAY_OUT,
    )

    result = engine.compare(
        gemini_analysis=gemini,
        ollama_analysis=ollama,
    )

    field = next(
        field
        for field in result.fields
        if field.field.value == "action"
    )

    assert field.gemini_value == "pit_stop"
    assert field.ollama_value == "stay_out"
    assert field.agreement == AgreementLevel.DISAGREE


def test_target_lap_disagreement_is_detected():
    """Detecta desacuerdo cuando los modelos proponen vueltas objetivo diferentes."""

    engine = build_engine()

    gemini = build_analysis(
        provider=Provider.GEMINI,
        target_lap=20,
    )

    ollama = build_analysis(
        provider=Provider.OLLAMA,
        target_lap=23,
    )

    result = engine.compare(
        gemini_analysis=gemini,
        ollama_analysis=ollama,
    )

    field = next(
        field
        for field in result.fields
        if field.field.value == "target_lap"
    )

    assert field.gemini_value == 20
    assert field.ollama_value == 23
    assert field.agreement == AgreementLevel.DISAGREE
    assert result.target_lap_difference == 3


def test_none_target_laps_are_comparable():
    """Considera como acuerdo dos vueltas objetivo no determinadas."""

    engine = build_engine()

    gemini = build_analysis(
        provider=Provider.GEMINI,
        target_lap=None,
    )

    ollama = build_analysis(
        provider=Provider.OLLAMA,
        target_lap=None,
    )

    result = engine.compare(
        gemini_analysis=gemini,
        ollama_analysis=ollama,
    )

    field = next(
        field
        for field in result.fields
        if field.field.value == "target_lap"
    )

    assert field.gemini_value is None
    assert field.ollama_value is None
    assert field.agreement == AgreementLevel.AGREE
    assert result.target_lap_difference is None


def test_one_missing_tyre_compound_is_not_comparable():
    """Marca como no comparable cuando solo un modelo informa compuesto."""

    engine = build_engine()

    gemini = build_analysis(
        provider=Provider.GEMINI,
        tyre_compound=TyreCompound.MEDIUM,
    )

    ollama = build_analysis(
        provider=Provider.OLLAMA,
        tyre_compound=None,
    )

    result = engine.compare(
        gemini_analysis=gemini,
        ollama_analysis=ollama,
    )

    field = next(
        field
        for field in result.fields
        if field.field.value == "tyre_compound"
    )

    assert field.gemini_value == "medium"
    assert field.ollama_value is None
    assert field.agreement == AgreementLevel.NOT_COMPARABLE


# ============================================================================
# CONFIDENCE COMPARISON
# ============================================================================


@pytest.mark.parametrize(
    ("gemini_confidence", "ollama_confidence", "expected_agreement"),
    [
        (0.90, 0.90, AgreementLevel.AGREE),
        (0.90, 0.75, AgreementLevel.CLOSE),
        (0.90, 0.60, AgreementLevel.DISAGREE),
    ],
)
def test_confidence_difference_is_classified_correctly(
    gemini_confidence,
    ollama_confidence,
    expected_agreement,
):
    """Clasifica la diferencia de confianza según los umbrales definidos."""

    engine = build_engine()

    gemini = build_analysis(
        provider=Provider.GEMINI,
        confidence=gemini_confidence,
    )

    ollama = build_analysis(
        provider=Provider.OLLAMA,
        confidence=ollama_confidence,
    )

    result = engine.compare(
        gemini_analysis=gemini,
        ollama_analysis=ollama,
    )

    field = next(
        field
        for field in result.fields
        if field.field.value == "confidence"
    )

    assert field.gemini_value == gemini_confidence
    assert field.ollama_value == ollama_confidence
    assert field.agreement == expected_agreement

    assert (
        result.confidence_difference
        == abs(gemini_confidence - ollama_confidence)
    )


# ============================================================================
# STRATEGIC AGREEMENT
# ============================================================================


def test_same_action_produces_strategic_agreement():
    """Considera que existe acuerdo estratégico cuando ambos proponen la misma acción."""

    engine = build_engine()

    gemini = build_analysis(
        provider=Provider.GEMINI,
        action=RecommendationAction.PIT_STOP,
    )

    ollama = build_analysis(
        provider=Provider.OLLAMA,
        action=RecommendationAction.PIT_STOP,
    )

    result = engine.compare(
        gemini_analysis=gemini,
        ollama_analysis=ollama,
    )

    assert result.strategic_agreement == AgreementLevel.AGREE


def test_different_action_produces_strategic_disagreement():
    """Considera que existe desacuerdo estratégico cuando las acciones difieren."""

    engine = build_engine()

    gemini = build_analysis(
        provider=Provider.GEMINI,
        action=RecommendationAction.PIT_STOP,
    )

    ollama = build_analysis(
        provider=Provider.OLLAMA,
        action=RecommendationAction.STAY_OUT,
    )

    result = engine.compare(
        gemini_analysis=gemini,
        ollama_analysis=ollama,
    )

    assert result.strategic_agreement == AgreementLevel.DISAGREE


# ============================================================================
# HELPERS
# ============================================================================


def test_target_lap_difference_is_calculated():
    """Calcula correctamente la diferencia absoluta entre vueltas objetivo."""

    engine = build_engine()

    gemini = build_analysis(
        provider=Provider.GEMINI,
        target_lap=18,
    )

    ollama = build_analysis(
        provider=Provider.OLLAMA,
        target_lap=23,
    )

    result = engine.compare(
        gemini_analysis=gemini,
        ollama_analysis=ollama,
    )

    assert result.target_lap_difference == 5


def test_target_lap_difference_is_none_when_one_lap_is_missing():
    """No calcula diferencia si alguno de los modelos no define vuelta objetivo."""

    engine = build_engine()

    gemini = build_analysis(
        provider=Provider.GEMINI,
        target_lap=20,
    )

    ollama = build_analysis(
        provider=Provider.OLLAMA,
        target_lap=None,
    )

    result = engine.compare(
        gemini_analysis=gemini,
        ollama_analysis=ollama,
    )

    assert result.target_lap_difference is None