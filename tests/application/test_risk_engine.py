import pytest

from core.application.risk_engine import RiskEngine

from core.domain.enums import (
    AgreementLevel,
    AnalysisCategory,
    AnalysisStatus,
    AnalysisUrgency,
    ComparisonStatus,
    Provider,
    RecommendationAction,
    RiskFactorType,
    RiskLevel,
    TyreCompound,
    RaceSession,
    EventType,
)

from core.domain.schemas import (
    AIAnalysis,
    Comparison,
    ModelMetrics,
    RaceEvent,
    Recommendation,
)


# ============================================================================
# HELPERS
# ============================================================================

def build_metrics() -> ModelMetrics:
    return ModelMetrics(
        input_tokens=100,
        output_tokens=50,
        total_tokens=150,
        latency_ms=100.0,
        cost=0.0,
        retries=0,
    )


def build_recommendation() -> Recommendation:
    return Recommendation(
        action=RecommendationAction.PIT_STOP,
        target_lap=20,
        tyre_compound=TyreCompound.MEDIUM,
        confidence=0.90,
        rationale="Pit stop is strategically recommended",
    )


def build_analysis(
    *,
    provider: Provider,
    status: AnalysisStatus = AnalysisStatus.SUCCESS,
    confidence: float = 0.90,
) -> AIAnalysis:
    return AIAnalysis(
        provider=provider,
        model="test-model",
        status=status,
        category=AnalysisCategory.RACE_STRATEGY,
        urgency=AnalysisUrgency.MEDIUM,
        confidence=confidence,
        summary="Strategic analysis.",
        reasoning="Strategic reasoning.",
        recommendation=build_recommendation(),
        metrics=build_metrics(),
        error=(
            "Provider failed."
            if status != AnalysisStatus.SUCCESS
            else None
        ),
    )


def build_event(
    *,
    event_type: EventType = EventType.STRATEGIC_OPPORTUNITY,
) -> RaceEvent:
    return RaceEvent(
        circuit="Monza",
        session=RaceSession.RACE,
        lap=20,
        driver="Driver",
        team="Team",
        position=5,
        event_type=event_type,
        description="Strategic race event.",
    )


def build_comparison(
    *,
    status: ComparisonStatus = ComparisonStatus.COMPLETED,
    agreement: AgreementLevel | None = AgreementLevel.AGREE,
    target_lap_difference: int | None = 0,
) -> Comparison:
    return Comparison(
        status=status,
        fields=[
            {
                "field": "category",
                "gemini_value": "race_strategy",
                "ollama_value": "race_strategy",
                "agreement": "agree",
            }
        ],
        strategic_agreement=agreement,
        confidence_difference=0.02,
        target_lap_difference=target_lap_difference,
    )


def build_engine() -> RiskEngine:
    return RiskEngine(confidence_threshold=0.80)


# ============================================================================
# INITIALIZATION
# ============================================================================

def test_engine_rejects_invalid_confidence_threshold():
    with pytest.raises(ValueError):
        RiskEngine(confidence_threshold=-0.1)

    with pytest.raises(ValueError):
        RiskEngine(confidence_threshold=1.1)


def test_engine_accepts_boundary_confidence_threshold():
    assert RiskEngine(confidence_threshold=0.0)
    assert RiskEngine(confidence_threshold=1.0)


# ============================================================================
# LOW RISK
# ============================================================================

def test_agreement_high_confidence_produces_low_risk():
    engine = build_engine()

    result = engine.assess(
        race_event=build_event(),
        gemini_analysis=build_analysis(
            provider=Provider.GEMINI,
            confidence=0.95,
        ),
        ollama_analysis=build_analysis(
            provider=Provider.OLLAMA,
            confidence=0.90,
        ),
        comparison=build_comparison(),
    )

    assert result.risk_score == 0
    assert result.risk_level == RiskLevel.LOW
    assert result.risk_factors == []


# ============================================================================
# PROVIDER FAILURE
# ============================================================================

def test_provider_failure_adds_high_risk():
    engine = build_engine()

    result = engine.assess(
        race_event=build_event(),
        gemini_analysis=build_analysis(
            provider=Provider.GEMINI,
            status=AnalysisStatus.ERROR,
        ),
        ollama_analysis=build_analysis(
            provider=Provider.OLLAMA,
        ),
        comparison=build_comparison(),
    )

    assert result.risk_score == 50
    assert result.risk_level == RiskLevel.HIGH
    assert result.risk_factors[0].type == RiskFactorType.PROVIDER_FAILURE


# ============================================================================
# MODEL DISAGREEMENT
# ============================================================================

def test_model_disagreement_adds_risk():
    engine = build_engine()

    result = engine.assess(
        race_event=build_event(),
        gemini_analysis=build_analysis(provider=Provider.GEMINI),
        ollama_analysis=build_analysis(provider=Provider.OLLAMA),
        comparison=build_comparison(
            agreement=AgreementLevel.DISAGREE,
        ),
    )

    assert result.risk_score == 25
    assert result.risk_level == RiskLevel.MEDIUM
    assert (
        result.risk_factors[0].type
        == RiskFactorType.MODEL_DISAGREEMENT
    )


# ============================================================================
# LOW CONFIDENCE
# ============================================================================

def test_low_confidence_adds_risk():
    engine = build_engine()

    result = engine.assess(
        race_event=build_event(),
        gemini_analysis=build_analysis(
            provider=Provider.GEMINI,
            confidence=0.70,
        ),
        ollama_analysis=build_analysis(
            provider=Provider.OLLAMA,
            confidence=0.90,
        ),
        comparison=build_comparison(),
    )

    assert result.risk_score == 30
    assert result.risk_level == RiskLevel.MEDIUM

    factor_types = {
        factor.type
        for factor in result.risk_factors
    }

    assert RiskFactorType.LOW_CONFIDENCE in factor_types
    assert RiskFactorType.CONFIDENCE_GAP in factor_types


# ============================================================================
# CONFIDENCE GAP
# ============================================================================

def test_large_confidence_gap_adds_risk():
    engine = build_engine()

    result = engine.assess(
        race_event=build_event(),
        gemini_analysis=build_analysis(
            provider=Provider.GEMINI,
            confidence=0.99,
        ),
        ollama_analysis=build_analysis(
            provider=Provider.OLLAMA,
            confidence=0.70,
        ),
        comparison=build_comparison(),
    )

    assert result.risk_score == 30
    assert result.risk_level == RiskLevel.MEDIUM

    factor_types = {
        factor.type
        for factor in result.risk_factors
    }

    assert RiskFactorType.LOW_CONFIDENCE in factor_types
    assert RiskFactorType.CONFIDENCE_GAP in factor_types


# ============================================================================
# TIMING
# ============================================================================

def test_target_lap_disagreement_adds_risk():
    engine = build_engine()

    result = engine.assess(
        race_event=build_event(),
        gemini_analysis=build_analysis(provider=Provider.GEMINI),
        ollama_analysis=build_analysis(provider=Provider.OLLAMA),
        comparison=build_comparison(
            target_lap_difference=3,
        ),
    )

    assert result.risk_score == 10
    assert result.risk_level == RiskLevel.LOW
    assert (
        result.risk_factors[0].type
        == RiskFactorType.TIMING_DISAGREEMENT
    )


# ============================================================================
# EVENT CRITICALITY
# ============================================================================

@pytest.mark.parametrize(
    "event_type",
    [
        EventType.MECHANICAL_ISSUE,
        EventType.SAFETY_CAR,
        EventType.VIRTUAL_SAFETY_CAR,
        EventType.RACE_INCIDENT,
    ],
)
def test_critical_event_adds_risk(event_type):
    engine = build_engine()

    result = engine.assess(
        race_event=build_event(event_type=event_type),
        gemini_analysis=build_analysis(provider=Provider.GEMINI),
        ollama_analysis=build_analysis(provider=Provider.OLLAMA),
        comparison=build_comparison(),
    )

    assert result.risk_score == 20
    assert result.risk_level == RiskLevel.LOW
    assert (
        result.risk_factors[0].type
        == RiskFactorType.EVENT_CRITICALITY
    )


# ============================================================================
# INSUFFICIENT INFORMATION
# ============================================================================

def test_insufficient_comparison_adds_risk():
    engine = build_engine()

    result = engine.assess(
        race_event=build_event(),
        gemini_analysis=build_analysis(provider=Provider.GEMINI),
        ollama_analysis=build_analysis(provider=Provider.OLLAMA),
        comparison=build_comparison(
            status=ComparisonStatus.INSUFFICIENT_DATA,
            agreement=None,
            target_lap_difference=None,
        ),
    )

    assert result.risk_score == 20
    assert result.risk_level == RiskLevel.LOW
    assert (
        result.risk_factors[0].type
        == RiskFactorType.INSUFFICIENT_INFORMATION
    )


# ============================================================================
# SCORE BOUNDARIES
# ============================================================================

@pytest.mark.parametrize(
    ("score", "expected"),
    [
        (0, RiskLevel.LOW),
        (24, RiskLevel.LOW),
        (25, RiskLevel.MEDIUM),
        (49, RiskLevel.MEDIUM),
        (50, RiskLevel.HIGH),
        (74, RiskLevel.HIGH),
        (75, RiskLevel.CRITICAL),
        (100, RiskLevel.CRITICAL),
    ],
)
def test_risk_level_boundaries(score, expected):
    assert RiskEngine._risk_level_from_score(score) == expected