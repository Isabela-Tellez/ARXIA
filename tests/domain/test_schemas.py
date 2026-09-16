from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from domain.enums import (
    AgreementLevel, AnalysisCategory, AnalysisStatus, AnalysisUrgency, ComparisonField,
    ComparisonStatus, DecisionReason, DecisionType, EventType, Provider, RaceSession,
    RecommendationAction, ReviewStatus, RiskFactorType, RiskLevel, TyreCompound,
    WeatherCondition,
)
from domain.schemas import (
    AIAnalysis, ArxiaDecision, ArxiaResult, Comparison, FieldComparison, HumanReview,
    ModelMetrics, RaceEvent, Recommendation, RiskAssessment, RiskFactor, WeatherData,
)


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def weather_data():
    """Datos meteorológicos válidos."""
    return WeatherData(
        condition=WeatherCondition.DRY,
        temperature_c=24.0,
        track_temperature_c=42.0,
        rain_probability=0.20,
        wind_speed_kmh=12.0,
    )


@pytest.fixture
def model_metrics():
    """Métricas válidas de ejecución."""
    return ModelMetrics(
        input_tokens=500,
        output_tokens=300,
        total_tokens=800,
        latency_ms=842.0,
        cost=0.0021,
        retries=0,
    )


@pytest.fixture
def recommendation():
    """Recomendación estratégica válida."""
    return Recommendation(
        action=RecommendationAction.PIT_STOP,
        target_lap=40,
        tyre_compound=TyreCompound.INTERMEDIATE,
        confidence=0.91,
        rationale="Pit stop is recommended before expected rainfall intensifies.",
        alternative_action=RecommendationAction.STAY_OUT,
    )


@pytest.fixture
def race_event(weather_data):
    """RaceEvent válido."""
    return RaceEvent(
        circuit="Barcelona",
        session=RaceSession.RACE,
        lap=38,
        driver="Charles Leclerc",
        team="Ferrari",
        position=4,
        weather=weather_data,
        event_type=EventType.TYRE_DEGRADATION,
        tyre_compound=TyreCompound.MEDIUM,
        track_condition=WeatherCondition.DRY,
        race_context="Rain is approaching and the pit window is opening.",
        description="Rear tyres are showing rapid degradation.",
    )


@pytest.fixture
def gemini_analysis(recommendation, model_metrics):
    """Análisis válido de Gemini."""
    return AIAnalysis(
        provider=Provider.GEMINI,
        model="gemini-2.5-pro",
        status=AnalysisStatus.SUCCESS,
        category=AnalysisCategory.TYRE_STRATEGY,
        urgency=AnalysisUrgency.HIGH,
        confidence=0.91,
        summary="Pit stop recommended before tyre degradation increases.",
        reasoning="Current tyre degradation and weather conditions indicate a narrow pit window.",
        recommendation=recommendation,
        metrics=model_metrics,
    )


@pytest.fixture
def ollama_analysis():
    """Análisis válido de OLLAMA."""
    return AIAnalysis(
        provider=Provider.OLLAMA,
        model="ollama-5",
        status=AnalysisStatus.SUCCESS,
        category=AnalysisCategory.TYRE_STRATEGY,
        urgency=AnalysisUrgency.HIGH,
        confidence=0.87,
        summary="Pit stop recommended with intermediate tyres soon.",
        reasoning="Tyre degradation combined with increasing rain probability supports a pit stop.",
        recommendation=Recommendation(
            action=RecommendationAction.PIT_STOP,
            target_lap=41,
            tyre_compound=TyreCompound.INTERMEDIATE,
            confidence=0.87,
            rationale="The pit window should open within the next few laps.",
            alternative_action=RecommendationAction.STAY_OUT,
        ),
        metrics=ModelMetrics(
            input_tokens=480,
            output_tokens=320,
            total_tokens=800,
            latency_ms=631.0,
            cost=0.0018,
            retries=0,
        ),
    )


@pytest.fixture
def comparison():
    """Comparación válida entre Gemini y OLLAMA."""
    fields = [
        (
            ComparisonField.CATEGORY,
            AnalysisCategory.TYRE_STRATEGY.value,
            AnalysisCategory.TYRE_STRATEGY.value,
            AgreementLevel.AGREE,
        ),
        (
            ComparisonField.URGENCY,
            AnalysisUrgency.HIGH.value,
            AnalysisUrgency.HIGH.value,
            AgreementLevel.AGREE,
        ),
        (
            ComparisonField.ACTION,
            RecommendationAction.PIT_STOP.value,
            RecommendationAction.PIT_STOP.value,
            AgreementLevel.AGREE,
        ),
        (
            ComparisonField.TARGET_LAP,
            40,
            41,
            AgreementLevel.CLOSE,
        ),
        (
            ComparisonField.TYRE_COMPOUND,
            TyreCompound.INTERMEDIATE.value,
            TyreCompound.INTERMEDIATE.value,
            AgreementLevel.AGREE,
        ),
        (
            ComparisonField.CONFIDENCE,
            0.91,
            0.87,
            AgreementLevel.CLOSE,
        ),
    ]

    return Comparison(
        status=ComparisonStatus.COMPLETED,
        fields=[
            FieldComparison(
                field=field,
                gemini_value=gemini,
                ollama_value=ollama,
                agreement=agreement,
            )
            for field, gemini, ollama, agreement in fields
        ],
        strategic_agreement=AgreementLevel.AGREE,
        confidence_difference=0.04,
        target_lap_difference=1,
    )


@pytest.fixture
def risk_assessment():
    """RiskAssessment válido."""
    return RiskAssessment(
        risk_score=18,
        risk_level=RiskLevel.LOW,
        risk_factors=[
            RiskFactor(
                type=RiskFactorType.CONFIDENCE_GAP,
                score=5,
                severity=RiskLevel.LOW,
                description="The confidence gap between models is small.",
            ),
            RiskFactor(
                type=RiskFactorType.TIMING_DISAGREEMENT,
                score=0,
                severity=RiskLevel.LOW,
                description="Models recommend nearly identical timing.",
            ),
        ],
        explanation="Models strongly agree and the calculated automation risk is low.",
    )


@pytest.fixture
def automatic_decision():
    """Decisión automática válida."""
    return ArxiaDecision(
        action=RecommendationAction.PIT_STOP,
        target_lap=40,
        tyre_compound=TyreCompound.INTERMEDIATE,
        confidence=0.89,
        decision=DecisionType.AUTOMATIC,
        risk_level=RiskLevel.LOW,
        reason=DecisionReason.LOW_RISK,
        supporting_models=[
            Provider.GEMINI,
            Provider.OLLAMA,
        ],
        rationale="Both models agree strategically and automation risk is low.",
    )


# =============================================================================
# WEATHER DATA
# =============================================================================

class TestWeatherData:
    """Tests de WeatherData."""

    def test_valid(self, weather_data):
        """Verifica que los datos meteorológicos válidos se aceptan."""
        assert weather_data.condition == WeatherCondition.DRY
        assert weather_data.rain_probability == 0.20

    @pytest.mark.parametrize(
        "field,value",
        [
            ("rain_probability", -0.1),
            ("rain_probability", 1.1),
            ("wind_speed_kmh", -1),
        ],
    )
    def test_invalid_values(self, field, value):
        """Verifica que los valores meteorológicos inválidos se rechazan."""
        with pytest.raises(ValidationError):
            WeatherData(
                condition=WeatherCondition.DRY,
                **{field: value},
            )


# =============================================================================
# MODEL METRICS
# =============================================================================

class TestModelMetrics:
    """Tests de ModelMetrics."""

    def test_valid(self, model_metrics):
        """Verifica que las métricas válidas se aceptan."""
        assert model_metrics.total_tokens == 800
        assert model_metrics.input_tokens + model_metrics.output_tokens == 800

    def test_total_tokens_must_match(self):
        """Verifica que total_tokens coincida con input + output."""
        with pytest.raises(
            ValidationError,
            match="Total tokens must equal input tokens plus output tokens",
        ):
            ModelMetrics(
                input_tokens=500,
                output_tokens=300,
                total_tokens=900,
                latency_ms=100,
                cost=0.01,
                retries=0,
            )

    @pytest.mark.parametrize(
        "kwargs",
        [
            {
                "input_tokens": -1,
                "output_tokens": 300,
                "total_tokens": 299,
            },
            {
                "input_tokens": 100,
                "output_tokens": 100,
                "total_tokens": 200,
                "latency_ms": -1,
            },
            {
                "input_tokens": 100,
                "output_tokens": 100,
                "total_tokens": 200,
                "cost": -0.01,
            },
            {
                "input_tokens": 100,
                "output_tokens": 100,
                "total_tokens": 200,
                "retries": -1,
            },
        ],
    )
    def test_negative_values_are_rejected(self, kwargs):
        """Verifica que los valores negativos se rechazan."""
        data = {
            "input_tokens": 100,
            "output_tokens": 100,
            "total_tokens": 200,
            "latency_ms": 100,
            "cost": 0.01,
            "retries": 0,
        }

        data.update(kwargs)

        with pytest.raises(ValidationError):
            ModelMetrics(**data)


# =============================================================================
# RECOMMENDATION
# =============================================================================

class TestRecommendation:
    """Tests de Recommendation."""

    def test_valid(self, recommendation):
        """Verifica que una recomendación válida se acepta."""
        assert recommendation.action == RecommendationAction.PIT_STOP
        assert recommendation.target_lap == 40
        assert recommendation.tyre_compound == TyreCompound.INTERMEDIATE

    @pytest.mark.parametrize(
        "kwargs",
        [
            {"confidence": -0.1},
            {"confidence": 1.1},
            {
                "target_lap": 0,
                "confidence": 0.8,
            },
            {
                "confidence": 0.8,
                "rationale": "   ",
            },
        ],
    )
    def test_invalid_values(self, kwargs):
        """Verifica que los valores inválidos se rechazan."""
        data = {
            "action": RecommendationAction.PIT_STOP,
            "confidence": 0.8,
            "rationale": "Valid rationale.",
        }

        data.update(kwargs)

        with pytest.raises(ValidationError):
            Recommendation(**data)


# =============================================================================
# RACE EVENT
# =============================================================================

class TestRaceEvent:
    """Tests de RaceEvent."""

    def test_valid(self, race_event):
        """Verifica que un evento de carrera válido se acepta."""
        assert race_event.circuit == "Barcelona"
        assert race_event.session == RaceSession.RACE
        assert race_event.lap == 38

    def test_text_is_normalized(self):
        """Verifica que los campos de texto se normalizan."""
        event = RaceEvent(
            circuit="  Barcelona   ",
            session=RaceSession.RACE,
            lap=38,
            driver="  Charles   Leclerc ",
            team=" Ferrari ",
            position=4,
            event_type=EventType.TYRE_DEGRADATION,
            description="  Rear tyres   are degrading rapidly. ",
        )

        assert event.circuit == "Barcelona"
        assert event.driver == "Charles Leclerc"
        assert event.team == "Ferrari"
        assert event.description == "Rear tyres are degrading rapidly."

    @pytest.mark.parametrize(
        "field,value",
        [
            ("lap", 0),
            ("position", 0),
        ],
    )
    def test_positive_fields(self, field, value):
        """Verifica que lap y position deben ser positivos."""
        data = {
            "circuit": "Barcelona",
            "session": RaceSession.RACE,
            "lap": 38,
            "driver": "Charles Leclerc",
            "team": "Ferrari",
            "position": 4,
            "event_type": EventType.TYRE_DEGRADATION,
            "description": "Rear tyres are degrading rapidly.",
        }

        data[field] = value

        with pytest.raises(ValidationError):
            RaceEvent(**data)


# =============================================================================
# AI ANALYSIS
# =============================================================================

class TestAIAnalysis:
    """Tests de AIAnalysis."""

    def test_valid(self, gemini_analysis):
        """Verifica que un análisis exitoso se acepta."""
        assert gemini_analysis.provider == Provider.GEMINI
        assert gemini_analysis.status == AnalysisStatus.SUCCESS
        assert gemini_analysis.error is None

    def test_failed_requires_error(self, recommendation):
        """Verifica que un análisis fallido requiere un error."""
        metrics = ModelMetrics(
            input_tokens=100,
            output_tokens=100,
            total_tokens=200,
            latency_ms=500,
            cost=0.001,
            retries=1,
        )

        with pytest.raises(
            ValidationError,
            match="Failed analysis requires an error",
        ):
            AIAnalysis(
                provider=Provider.GEMINI,
                model="gemini-test",
                status=AnalysisStatus.TIMEOUT,
                category=AnalysisCategory.RACE_STRATEGY,
                urgency=AnalysisUrgency.HIGH,
                confidence=0.0,
                summary="Analysis failed.",
                reasoning="The provider timed out.",
                recommendation=recommendation,
                metrics=metrics,
            )

    def test_success_cannot_have_error(self, gemini_analysis):
        """Verifica que un análisis exitoso no puede contener un error."""
        data = gemini_analysis.model_dump()
        data["error"] = "Unexpected error."

        with pytest.raises(
            ValidationError,
            match="Successful analysis cannot contain an error",
        ):
            AIAnalysis(**data)


# =============================================================================
# FIELD COMPARISON
# =============================================================================

class TestFieldComparison:
    """Tests de FieldComparison."""

    @pytest.mark.parametrize(
        "agreement,gemini,ollama",
        [
            (
                AgreementLevel.AGREE,
                "pit_stop",
                "pit_stop",
            ),
            (
                AgreementLevel.DISAGREE,
                "pit_stop",
                "stay_out",
            ),
            (
                AgreementLevel.NOT_COMPARABLE,
                None,
                None,
            ),
        ],
    )
    def test_agreement(self, agreement, gemini, ollama):
        """Verifica los diferentes niveles de acuerdo."""
        result = FieldComparison(
            field=ComparisonField.ACTION,
            gemini_value=gemini,
            ollama_value=ollama,
            agreement=agreement,
        )

        assert result.agreement == agreement


# =============================================================================
# COMPARISON
# =============================================================================

class TestComparison:
    """Tests de Comparison."""

    def test_valid(self, comparison):
        """Verifica que una comparación completa se acepta."""
        assert comparison.status == ComparisonStatus.COMPLETED
        assert comparison.strategic_agreement == AgreementLevel.AGREE
        assert comparison.target_lap_difference == 1

    def test_completed_requires_fields(self):
        """Verifica que una comparación completada requiere campos."""
        with pytest.raises(
            ValidationError,
            match="Completed comparison requires field comparisons",
        ):
            Comparison(
                status=ComparisonStatus.COMPLETED,
                strategic_agreement=AgreementLevel.AGREE,
            )

    def test_completed_requires_strategic_agreement(self):
        """Verifica que una comparación completada requiere acuerdo estratégico."""
        with pytest.raises(
            ValidationError,
            match="Completed comparison requires strategic agreement",
        ):
            Comparison(
                status=ComparisonStatus.COMPLETED,
                fields=[
                    FieldComparison(
                        field=ComparisonField.ACTION,
                        gemini_value="pit_stop",
                        ollama_value="pit_stop",
                        agreement=AgreementLevel.AGREE,
                    )
                ],
            )

    def test_insufficient_data_cannot_have_agreement(self):
        """Verifica que datos insuficientes no pueden tener acuerdo estratégico."""
        with pytest.raises(ValidationError):
            Comparison(
                status=ComparisonStatus.INSUFFICIENT_DATA,
                strategic_agreement=AgreementLevel.AGREE,
            )

    def test_target_lap_difference_cannot_be_negative(self):
        """Verifica que la diferencia de vueltas no puede ser negativa."""
        with pytest.raises(ValidationError):
            Comparison(
                status=ComparisonStatus.COMPLETED,
                fields=[
                    FieldComparison(
                        field=ComparisonField.ACTION,
                        gemini_value="pit_stop",
                        ollama_value="pit_stop",
                        agreement=AgreementLevel.AGREE,
                    )
                ],
                strategic_agreement=AgreementLevel.AGREE,
                target_lap_difference=-1,
            )


# =============================================================================
# RISK FACTOR
# =============================================================================

class TestRiskFactor:
    """Tests de RiskFactor."""

    def test_valid(self):
        """Verifica que un factor de riesgo válido se acepta."""
        factor = RiskFactor(
            type=RiskFactorType.MODEL_DISAGREEMENT,
            score=40,
            severity=RiskLevel.HIGH,
            description="Models disagree.",
        )

        assert factor.score == 40
        assert factor.severity == RiskLevel.HIGH

    @pytest.mark.parametrize(
        "score",
        [
            -1,
            101,
        ],
    )
    def test_score_bounds(self, score):
        """Verifica que el score está limitado entre 0 y 100."""
        with pytest.raises(ValidationError):
            RiskFactor(
                type=RiskFactorType.MODEL_DISAGREEMENT,
                score=score,
                severity=RiskLevel.HIGH,
                description="Models disagree.",
            )


# =============================================================================
# RISK ASSESSMENT
# =============================================================================

class TestRiskAssessment:
    """Tests de RiskAssessment."""

    def test_valid(self, risk_assessment):
        """Verifica que una evaluación de riesgo válida se acepta."""
        assert risk_assessment.risk_score == 18
        assert risk_assessment.risk_level == RiskLevel.LOW

    @pytest.mark.parametrize(
        "score,level",
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
    def test_boundaries(self, score, level):
        """Verifica los límites de cada nivel de riesgo."""
        result = RiskAssessment(
            risk_score=score,
            risk_level=level,
            explanation="Risk level matches score.",
        )

        assert result.risk_level == level

    @pytest.mark.parametrize(
        "score",
        [
            -1,
            101,
        ],
    )
    def test_score_bounds(self, score):
        """Verifica que el risk_score está limitado entre 0 y 100."""
        with pytest.raises(ValidationError):
            RiskAssessment(
                risk_score=score,
                risk_level=RiskLevel.LOW,
                explanation="Invalid risk.",
            )

    def test_level_must_match_score(self):
        """Verifica que el nivel de riesgo coincide con el score."""
        with pytest.raises(
            ValidationError,
            match="Risk level does not match risk score",
        ):
            RiskAssessment(
                risk_score=80,
                risk_level=RiskLevel.HIGH,
                explanation="Incorrect risk level.",
            )

    def test_explanation_cannot_be_empty(self):
        """Verifica que la explicación no puede estar vacía."""
        with pytest.raises(ValidationError):
            RiskAssessment(
                risk_score=10,
                risk_level=RiskLevel.LOW,
                explanation="   ",
            )


# =============================================================================
# ARXIA DECISION
# =============================================================================

class TestArxiaDecision:
    """Tests de ArxiaDecision."""

    def test_valid(self, automatic_decision):
        """Verifica que una decisión automática válida se acepta."""
        assert automatic_decision.decision == DecisionType.AUTOMATIC
        assert automatic_decision.risk_level == RiskLevel.LOW

    @pytest.mark.parametrize(
        "risk",
        [
            RiskLevel.HIGH,
            RiskLevel.CRITICAL,
        ],
    )
    def test_high_risk_cannot_be_automatic(self, risk):
        """Verifica que riesgo alto o crítico requiere revisión humana."""
        reason = (
            DecisionReason.CRITICAL_RISK
            if risk == RiskLevel.CRITICAL
            else DecisionReason.HIGH_RISK
        )

        with pytest.raises(
            ValidationError,
            match="High or critical risk cannot result in automatic decision",
        ):
            ArxiaDecision(
                action=RecommendationAction.PIT_STOP,
                target_lap=40,
                tyre_compound=TyreCompound.INTERMEDIATE,
                confidence=0.9,
                decision=DecisionType.AUTOMATIC,
                risk_level=risk,
                reason=reason,
                supporting_models=[
                    Provider.GEMINI,
                    Provider.OLLAMA,
                ],
                rationale="High risk requires human review.",
            )

    def test_low_risk_should_not_require_review(self):
        """Verifica que el riesgo bajo no requiere revisión humana."""
        with pytest.raises(
            ValidationError,
            match="Low risk should not require human review",
        ):
            ArxiaDecision(
                action=RecommendationAction.PIT_STOP,
                target_lap=40,
                confidence=0.9,
                decision=DecisionType.HUMAN_REVIEW,
                risk_level=RiskLevel.LOW,
                reason=DecisionReason.LOW_RISK,
                rationale="This should remain automatic.",
            )


# =============================================================================
# HUMAN REVIEW
# =============================================================================

class TestHumanReview:
    """Tests de HumanReview."""

    def test_pending(self):
        """Verifica una revisión humana pendiente."""
        review = HumanReview(
            status=ReviewStatus.PENDING,
        )

        assert review.status == ReviewStatus.PENDING
        assert review.final_decision is None
        assert review.reviewed_at is None

    def test_pending_cannot_have_decision(self, recommendation):
        """Verifica que una revisión pendiente no puede tener decisión final."""
        with pytest.raises(ValidationError):
            HumanReview(
                status=ReviewStatus.PENDING,
                final_decision=recommendation,
            )

    def test_pending_cannot_have_reviewed_at(self):
        """Verifica que una revisión pendiente no puede tener fecha de revisión."""
        with pytest.raises(ValidationError):
            HumanReview(
                status=ReviewStatus.PENDING,
                reviewed_at=datetime.now(timezone.utc),
            )

    def test_completed_requires_decision(self):
        """Verifica que una revisión completada requiere decisión final."""
        with pytest.raises(
            ValidationError,
            match="Completed review requires final decision",
        ):
            HumanReview(
                status=ReviewStatus.ACCEPTED,
                reviewed_at=datetime.now(timezone.utc),
            )

    def test_completed_requires_reviewed_at(self, recommendation):
        """Verifica que una revisión completada requiere fecha de revisión."""
        with pytest.raises(
            ValidationError,
            match="Completed review requires reviewed_at",
        ):
            HumanReview(
                status=ReviewStatus.ACCEPTED,
                final_decision=recommendation,
            )

    def test_accepted(self, recommendation):
        """Verifica una revisión aceptada válida."""
        reviewed_at = datetime.now(timezone.utc)

        review = HumanReview(
            status=ReviewStatus.ACCEPTED,
            final_decision=recommendation,
            reviewer_comment="Accepted the ARXIA recommendation.",
            reviewed_at=reviewed_at,
        )

        assert review.status == ReviewStatus.ACCEPTED
        assert review.final_decision == recommendation
        assert review.reviewed_at == reviewed_at

    def test_corrected(self):
        """Verifica una revisión corregida válida."""
        decision = Recommendation(
            action=RecommendationAction.STAY_OUT,
            target_lap=45,
            confidence=1.0,
            rationale="Track is expected to dry.",
        )

        review = HumanReview(
            status=ReviewStatus.CORRECTED,
            final_decision=decision,
            reviewer_comment="Track expected to dry.",
            reviewed_at=datetime.now(timezone.utc),
        )

        assert review.status == ReviewStatus.CORRECTED
        assert review.final_decision.action == RecommendationAction.STAY_OUT


# =============================================================================
# ARXIA RESULT
# =============================================================================

class TestArxiaResult:
    """Tests de ArxiaResult."""

    def test_valid_automatic_result(
        self,
        race_event,
        gemini_analysis,
        ollama_analysis,
        comparison,
        risk_assessment,
        automatic_decision,
    ):
        """Verifica que un resultado automático completo es válido."""
        result = ArxiaResult(
            race_event=race_event,
            gemini_analysis=gemini_analysis,
            ollama_analysis=ollama_analysis,
            comparison=comparison,
            risk_assessment=risk_assessment,
            decision=automatic_decision,
        )

        assert result.gemini_analysis.provider == Provider.GEMINI
        assert result.ollama_analysis.provider == Provider.OLLAMA
        assert result.human_review is None

    def test_automatic_cannot_have_review(
        self,
        race_event,
        gemini_analysis,
        ollama_analysis,
        comparison,
        risk_assessment,
        automatic_decision,
    ):
        """Verifica que una decisión automática no puede tener revisión humana."""
        with pytest.raises(
            ValidationError,
            match="Automatic decision cannot have human review",
        ):
            ArxiaResult(
                race_event=race_event,
                gemini_analysis=gemini_analysis,
                ollama_analysis=ollama_analysis,
                comparison=comparison,
                risk_assessment=risk_assessment,
                decision=automatic_decision,
                human_review=HumanReview(
                    status=ReviewStatus.PENDING,
                ),
            )

    def test_human_review_decision_requires_review(
        self,
        race_event,
        gemini_analysis,
        ollama_analysis,
        comparison,
    ):
        """Verifica que una decisión de revisión requiere HumanReview."""
        risk = RiskAssessment(
            risk_score=72,
            risk_level=RiskLevel.HIGH,
            risk_factors=[
                RiskFactor(
                    type=RiskFactorType.MODEL_DISAGREEMENT,
                    score=40,
                    severity=RiskLevel.HIGH,
                    description="Models disagree.",
                )
            ],
            explanation="High automation risk requires review.",
        )

        decision = ArxiaDecision(
            action=RecommendationAction.PIT_STOP,
            target_lap=40,
            tyre_compound=TyreCompound.INTERMEDIATE,
            confidence=0.70,
            decision=DecisionType.HUMAN_REVIEW,
            risk_level=RiskLevel.HIGH,
            reason=DecisionReason.MODEL_DISAGREEMENT,
            supporting_models=[
                Provider.GEMINI,
                Provider.OLLAMA,
            ],
            rationale="Human review is required.",
        )

        with pytest.raises(
            ValidationError,
            match="Human review decision requires human review",
        ):
            ArxiaResult(
                race_event=race_event,
                gemini_analysis=gemini_analysis,
                ollama_analysis=ollama_analysis,
                comparison=comparison,
                risk_assessment=risk,
                decision=decision,
            )

    def test_valid_human_review_result(
        self,
        race_event,
        gemini_analysis,
        ollama_analysis,
        comparison,
    ):
        """Verifica que un resultado con revisión humana es válido."""
        risk = RiskAssessment(
            risk_score=72,
            risk_level=RiskLevel.HIGH,
            risk_factors=[
                RiskFactor(
                    type=RiskFactorType.MODEL_DISAGREEMENT,
                    score=40,
                    severity=RiskLevel.HIGH,
                    description="Models disagree.",
                ),
                RiskFactor(
                    type=RiskFactorType.EVENT_CRITICALITY,
                    score=20,
                    severity=RiskLevel.MEDIUM,
                    description="Event affects race strategy.",
                ),
            ],
            explanation="High automation risk requires engineer review.",
        )

        decision = ArxiaDecision(
            action=RecommendationAction.PIT_STOP,
            target_lap=40,
            tyre_compound=TyreCompound.INTERMEDIATE,
            confidence=0.70,
            decision=DecisionType.HUMAN_REVIEW,
            risk_level=RiskLevel.HIGH,
            reason=DecisionReason.MODEL_DISAGREEMENT,
            supporting_models=[
                Provider.GEMINI,
                Provider.OLLAMA,
            ],
            rationale="Models disagree and human review is required.",
        )

        result = ArxiaResult(
            race_event=race_event,
            gemini_analysis=gemini_analysis,
            ollama_analysis=ollama_analysis,
            comparison=comparison,
            risk_assessment=risk,
            decision=decision,
            human_review=HumanReview(
                status=ReviewStatus.PENDING,
            ),
        )

        assert result.decision.decision == DecisionType.HUMAN_REVIEW
        assert result.human_review.status == ReviewStatus.PENDING

    def test_gemini_must_use_gemini_provider(
        self,
        race_event,
        gemini_analysis,
        ollama_analysis,
        comparison,
        risk_assessment,
        automatic_decision,
    ):
        """Verifica que gemini_analysis usa el provider GEMINI."""
        with pytest.raises(
            ValidationError,
            match="gemini_analysis must use GEMINI provider",
        ):
            ArxiaResult(
                race_event=race_event,
                gemini_analysis=gemini_analysis.model_copy(
                    update={"provider": Provider.OLLAMA}
                ),
                ollama_analysis=ollama_analysis,
                comparison=comparison,
                risk_assessment=risk_assessment,
                decision=automatic_decision,
            )

    def test_ollama_must_use_ollama_provider(
        self,
        race_event,
        gemini_analysis,
        ollama_analysis,
        comparison,
        risk_assessment,
        automatic_decision,
    ):
        """Verifica que ollama_analysis usa el provider OLLAMA."""
        with pytest.raises(
            ValidationError,
            match="ollama_analysis must use OLLAMA provider",
        ):
            ArxiaResult(
                race_event=race_event,
                gemini_analysis=gemini_analysis,
                ollama_analysis=ollama_analysis.model_copy(
                    update={"provider": Provider.GEMINI}
                ),
                comparison=comparison,
                risk_assessment=risk_assessment,
                decision=automatic_decision,
            )