import pytest

from core.application.decision_engine import DecisionEngine
from core.domain.enums import (
    AgreementLevel,
    AnalysisCategory,
    AnalysisStatus,
    AnalysisUrgency,
    ComparisonStatus,
    DecisionReason,
    DecisionType,
    Provider,
    RecommendationAction,
    RiskLevel,
    TyreCompound,
)
from core.domain.schemas import (
    AIAnalysis,
    Comparison,
    ModelMetrics,
    Recommendation,
    RiskAssessment,
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


def build_recommendation(
    *,
    action: RecommendationAction = RecommendationAction.PIT_STOP,
    target_lap: int | None = 20,
    tyre_compound: TyreCompound | None = TyreCompound.MEDIUM,
    confidence: float = 0.90,
) -> Recommendation:
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
    recommendation_confidence: float = 0.90,
    action: RecommendationAction = RecommendationAction.PIT_STOP,
    target_lap: int | None = 20,
    tyre_compound: TyreCompound | None = TyreCompound.MEDIUM,
    error: str | None = None,
) -> AIAnalysis:
    return AIAnalysis(
        provider=provider,
        model="test-model",
        status=status,
        category=AnalysisCategory.RACE_STRATEGY,
        urgency=AnalysisUrgency.MEDIUM,
        confidence=confidence,
        summary="Strategic race analysis for the current situation.",
        reasoning="Both models evaluate the current race context.",
        recommendation=build_recommendation(
            action=action,
            target_lap=target_lap,
            tyre_compound=tyre_compound,
            confidence=recommendation_confidence,
        ),
        metrics=build_metrics(),
        error=error,
    )


def build_comparison(
    *,
    status: ComparisonStatus = ComparisonStatus.COMPLETED,
    strategic_agreement: AgreementLevel | None = AgreementLevel.AGREE,
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
        strategic_agreement=strategic_agreement,
        confidence_difference=0.02,
        target_lap_difference=0,
    )


def build_risk(
    *,
    score: int = 10,
    level: RiskLevel = RiskLevel.LOW,
) -> RiskAssessment:
    return RiskAssessment(
        risk_score=score,
        risk_level=level,
        risk_factors=[],
        explanation="Low automation risk.",
    )


def build_engine(
    *,
    threshold: float = 0.80,
) -> DecisionEngine:
    return DecisionEngine(
        confidence_threshold=threshold,
    )


# ============================================================================
# INITIALIZATION
# ============================================================================


def test_engine_rejects_invalid_confidence_threshold():
    with pytest.raises(ValueError):
        DecisionEngine(confidence_threshold=-0.1)

    with pytest.raises(ValueError):
        DecisionEngine(confidence_threshold=1.1)


def test_engine_accepts_boundary_confidence_thresholds():
    assert DecisionEngine(confidence_threshold=0.0)
    assert DecisionEngine(confidence_threshold=1.0)


# ============================================================================
# PROVIDER FAILURE
# ============================================================================


def test_provider_failure_requires_human_review():
    engine = build_engine()

    gemini = build_analysis(
        provider=Provider.GEMINI,
        status=AnalysisStatus.ERROR,
        error="Gemini provider failed.",
    )

    ollama = build_analysis(
        provider=Provider.OLLAMA,
    )

    result = engine.decide(
        gemini_analysis=gemini,
        ollama_analysis=ollama,
        comparison=build_comparison(),
        risk_assessment=build_risk(),
    )

    assert result.decision == DecisionType.HUMAN_REVIEW
    assert result.reason == DecisionReason.PROVIDER_FAILURE
    assert result.risk_level == RiskLevel.HIGH


# ============================================================================
# RISK
# ============================================================================


@pytest.mark.parametrize(
    ("risk_level", "reason"),
    [
        (RiskLevel.HIGH, DecisionReason.HIGH_RISK),
        (RiskLevel.CRITICAL, DecisionReason.CRITICAL_RISK),
    ],
)
def test_high_or_critical_risk_requires_human_review(
    risk_level,
    reason,
):
    engine = build_engine()

    gemini = build_analysis(provider=Provider.GEMINI)
    ollama = build_analysis(provider=Provider.OLLAMA)

    score = {
        RiskLevel.HIGH: 60,
        RiskLevel.CRITICAL: 90,
    }[risk_level]

    result = engine.decide(
        gemini_analysis=gemini,
        ollama_analysis=ollama,
        comparison=build_comparison(),
        risk_assessment=build_risk(
            score=score,
            level=risk_level,
        ),
    )

    assert result.decision == DecisionType.HUMAN_REVIEW
    assert result.reason == reason
    assert result.risk_level == risk_level


def test_medium_risk_requires_human_review():
    engine = build_engine()

    gemini = build_analysis(provider=Provider.GEMINI)
    ollama = build_analysis(provider=Provider.OLLAMA)

    result = engine.decide(
        gemini_analysis=gemini,
        ollama_analysis=ollama,
        comparison=build_comparison(),
        risk_assessment=build_risk(
            score=30,
            level=RiskLevel.MEDIUM,
        ),
    )

    assert result.decision == DecisionType.HUMAN_REVIEW
    assert result.reason == DecisionReason.INSUFFICIENT_INFORMATION
    assert result.risk_level == RiskLevel.MEDIUM


# ============================================================================
# COMPARISON
# ============================================================================


def test_incomplete_comparison_requires_human_review():
    engine = build_engine()

    gemini = build_analysis(provider=Provider.GEMINI)
    ollama = build_analysis(provider=Provider.OLLAMA)

    comparison = build_comparison(
        status=ComparisonStatus.INSUFFICIENT_DATA,
        strategic_agreement=None,
    )

    result = engine.decide(
        gemini_analysis=gemini,
        ollama_analysis=ollama,
        comparison=comparison,
        risk_assessment=build_risk(),
    )

    assert result.decision == DecisionType.HUMAN_REVIEW
    assert result.reason == DecisionReason.MODEL_DISAGREEMENT
    assert result.risk_level == RiskLevel.MEDIUM


def test_model_disagreement_requires_human_review():
    engine = build_engine()

    gemini = build_analysis(provider=Provider.GEMINI)
    ollama = build_analysis(provider=Provider.OLLAMA)

    comparison = build_comparison(
        strategic_agreement=AgreementLevel.DISAGREE,
    )

    result = engine.decide(
        gemini_analysis=gemini,
        ollama_analysis=ollama,
        comparison=comparison,
        risk_assessment=build_risk(),
    )

    assert result.decision == DecisionType.HUMAN_REVIEW
    assert result.reason == DecisionReason.MODEL_DISAGREEMENT
    assert result.risk_level == RiskLevel.MEDIUM


# ============================================================================
# CONFIDENCE
# ============================================================================


def test_low_model_confidence_requires_human_review():
    engine = build_engine(threshold=0.80)

    gemini = build_analysis(
        provider=Provider.GEMINI,
        confidence=0.70,
        recommendation_confidence=0.90,
    )

    ollama = build_analysis(
        provider=Provider.OLLAMA,
        confidence=0.95,
        recommendation_confidence=0.95,
    )

    result = engine.decide(
        gemini_analysis=gemini,
        ollama_analysis=ollama,
        comparison=build_comparison(),
        risk_assessment=build_risk(),
    )

    assert result.decision == DecisionType.HUMAN_REVIEW
    assert result.reason == DecisionReason.LOW_CONFIDENCE
    assert result.risk_level == RiskLevel.MEDIUM


def test_low_recommendation_confidence_requires_human_review():
    engine = build_engine(threshold=0.80)

    gemini = build_analysis(
        provider=Provider.GEMINI,
        confidence=0.95,
        recommendation_confidence=0.70,
    )

    ollama = build_analysis(
        provider=Provider.OLLAMA,
        confidence=0.95,
        recommendation_confidence=0.95,
    )

    result = engine.decide(
        gemini_analysis=gemini,
        ollama_analysis=ollama,
        comparison=build_comparison(),
        risk_assessment=build_risk(),
    )

    assert result.decision == DecisionType.HUMAN_REVIEW
    assert result.reason == DecisionReason.LOW_CONFIDENCE


def test_confidence_exactly_at_threshold_is_accepted():
    engine = build_engine(threshold=0.80)

    gemini = build_analysis(
        provider=Provider.GEMINI,
        confidence=0.80,
        recommendation_confidence=0.80,
    )

    ollama = build_analysis(
        provider=Provider.OLLAMA,
        confidence=0.80,
        recommendation_confidence=0.80,
    )

    result = engine.decide(
        gemini_analysis=gemini,
        ollama_analysis=ollama,
        comparison=build_comparison(),
        risk_assessment=build_risk(),
    )

    assert result.decision == DecisionType.AUTOMATIC


# ============================================================================
# AUTOMATIC DECISION
# ============================================================================


def test_agreement_low_risk_and_high_confidence_produces_automatic_decision():
    engine = build_engine()

    gemini = build_analysis(
        provider=Provider.GEMINI,
        confidence=0.95,
        recommendation_confidence=0.92,
    )

    ollama = build_analysis(
        provider=Provider.OLLAMA,
        confidence=0.90,
        recommendation_confidence=0.88,
    )

    result = engine.decide(
        gemini_analysis=gemini,
        ollama_analysis=ollama,
        comparison=build_comparison(),
        risk_assessment=build_risk(),
    )

    assert result.decision == DecisionType.AUTOMATIC
    assert result.reason == DecisionReason.MODELS_AGREE
    assert result.risk_level == RiskLevel.LOW

    assert result.action == RecommendationAction.PIT_STOP
    assert result.target_lap == 20
    assert result.tyre_compound == TyreCompound.MEDIUM

    assert result.confidence == 0.88


# ============================================================================
# ACTION SELECTION
# ============================================================================


def test_matching_actions_are_selected():
    engine = build_engine()

    gemini = build_analysis(
        provider=Provider.GEMINI,
        action=RecommendationAction.PUSH,
    )

    ollama = build_analysis(
        provider=Provider.OLLAMA,
        action=RecommendationAction.PUSH,
    )

    result = engine.decide(
        gemini_analysis=gemini,
        ollama_analysis=ollama,
        comparison=build_comparison(),
        risk_assessment=build_risk(),
    )

    assert result.action == RecommendationAction.PUSH


# ============================================================================
# TARGET LAP
# ============================================================================


def test_matching_target_laps_are_selected():
    engine = build_engine()

    gemini = build_analysis(
        provider=Provider.GEMINI,
        target_lap=25,
    )

    ollama = build_analysis(
        provider=Provider.OLLAMA,
        target_lap=25,
    )

    result = engine.decide(
        gemini_analysis=gemini,
        ollama_analysis=ollama,
        comparison=build_comparison(),
        risk_assessment=build_risk(),
    )

    assert result.target_lap == 25


# ============================================================================
# TYRE COMPOUND
# ============================================================================


def test_matching_tyre_compounds_are_selected():
    engine = build_engine()

    gemini = build_analysis(
        provider=Provider.GEMINI,
        tyre_compound=TyreCompound.SOFT,
    )

    ollama = build_analysis(
        provider=Provider.OLLAMA,
        tyre_compound=TyreCompound.SOFT,
    )

    result = engine.decide(
        gemini_analysis=gemini,
        ollama_analysis=ollama,
        comparison=build_comparison(),
        risk_assessment=build_risk(),
    )

    assert result.tyre_compound == TyreCompound.SOFT


def test_missing_tyre_compound_from_one_model_uses_available_value():
    engine = build_engine()

    gemini = build_analysis(
        provider=Provider.GEMINI,
        tyre_compound=TyreCompound.SOFT,
    )

    ollama = build_analysis(
        provider=Provider.OLLAMA,
        tyre_compound=None,
    )

    result = engine.decide(
        gemini_analysis=gemini,
        ollama_analysis=ollama,
        comparison=build_comparison(),
        risk_assessment=build_risk(),
    )

    assert result.tyre_compound == TyreCompound.SOFT