"""
Schemas Pydantic del dominio de ARXIA.

Definen la estructura y validación de los datos utilizados por el
motor de decisión multimodelo de motorsport.
"""

from datetime import datetime, timezone
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator, model_validator

from .enums import (
    AgreementLevel,
    AnalysisCategory,
    AnalysisStatus,
    AnalysisUrgency,
    ComparisonField,
    ComparisonStatus,
    DecisionReason,
    DecisionType,
    EventType,
    Provider,
    RecommendationAction,
    ReviewStatus,
    RiskFactorType,
    RiskLevel,
    RaceSession,
    TyreCompound,
    WeatherCondition,
)


# ============================================================================
# WEATHER
# ============================================================================


class WeatherData(BaseModel):
    """Información meteorológica asociada a un RaceEvent."""

    condition: WeatherCondition = WeatherCondition.UNKNOWN

    temperature_c: float | None = None

    track_temperature_c: float | None = None

    rain_probability: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
    )

    wind_speed_kmh: float | None = Field(
        default=None,
        ge=0.0,
    )

    @field_validator("temperature_c", "track_temperature_c")
    @classmethod
    def validate_temperature(
        cls,
        value: float | None,
    ) -> float | None:
        if value is not None and not -100 <= value <= 100:
            raise ValueError(
                "Temperature is unrealistically low or high"
            )

        return value


# ============================================================================
# MODEL METRICS
# ============================================================================


class ModelMetrics(BaseModel):
    """Métricas asociadas a una ejecución de modelo."""

    input_tokens: int = Field(ge=0)

    output_tokens: int = Field(ge=0)

    total_tokens: int = Field(ge=0)

    latency_ms: float = Field(ge=0)

    cost: float = Field(ge=0)

    retries: int = Field(ge=0)

    @model_validator(mode="after")
    def validate_total_tokens(self):
        expected_total = self.input_tokens + self.output_tokens

        if self.total_tokens != expected_total:
            raise ValueError(
                "Total tokens must equal input tokens plus output tokens"
            )

        return self


# ============================================================================
# RECOMMENDATION
# ============================================================================


class Recommendation(BaseModel):
    """Recomendación estratégica producida por un modelo."""

    action: RecommendationAction

    target_lap: int | None = Field(
        default=None,
        ge=1,
    )

    tyre_compound: TyreCompound | None = None

    confidence: float = Field(
        ge=0.0,
        le=1.0,
    )

    rationale: str = Field(
        min_length=1,
    )

    alternative_action: RecommendationAction | None = None

    @field_validator("rationale")
    @classmethod
    def normalize_rationale(cls, value: str) -> str:
        value = " ".join(value.split())

        if not value:
            raise ValueError(
                "Recommendation rationale cannot be empty"
            )

        return value


# ============================================================================
# RACE EVENT
# ============================================================================


class RaceEvent(BaseModel):
    """Contexto completo del evento de carrera analizado por ARXIA."""

    id: UUID = Field(
        default_factory=uuid4,
    )

    circuit: str = Field(
        min_length=1,
    )

    session: RaceSession

    lap: int = Field(
        ge=1,
    )

    driver: str = Field(
        min_length=1,
    )

    team: str = Field(
        min_length=1,
    )

    position: int = Field(
        ge=1,
    )

    weather: WeatherData | None = None

    event_type: EventType

    tyre_compound: TyreCompound | None = None

    track_condition: WeatherCondition | None = None

    race_context: str | None = None

    description: str = Field(
        min_length=1,
    )

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
    )

    @field_validator(
        "circuit",
        "driver",
        "team",
        "description",
    )
    @classmethod
    def normalize_required_text(cls, value: str) -> str:
        value = " ".join(value.split())

        if not value:
            raise ValueError(
                "Text field cannot be empty"
            )

        return value

    @field_validator("race_context")
    @classmethod
    def normalize_race_context(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        value = " ".join(value.split())

        return value or None


# ============================================================================
# AI ANALYSIS
# ============================================================================

class AIAnalysis(BaseModel):
    """Análisis estructurado producido por un proveedor de IA."""

    provider: Provider
    model: str = Field(min_length=1)
    status: AnalysisStatus
    category: AnalysisCategory
    urgency: AnalysisUrgency
    confidence: float = Field(ge=0.0, le=1.0)
    summary: str = Field(min_length=1)
    reasoning: str = Field(min_length=1)
    recommendation: Recommendation
    metrics: ModelMetrics
    error: str | None = None

    @field_validator("model")
    @classmethod
    def normalize_model(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Model cannot be empty")
        return value

    @field_validator("summary", "reasoning")
    @classmethod
    def normalize_analysis_text(cls, value: str) -> str:
        value = " ".join(value.split())
        if not value:
            raise ValueError("Analysis text cannot be empty")
        return value

    @field_validator("error")
    @classmethod
    def validate_error(cls, value: str | None) -> str | None:
        if value is None:
            return None

        value = " ".join(value.split())

        if not value:
            raise ValueError("Error cannot be empty")

        return value

    @model_validator(mode="after")
    def validate_analysis(self):
        if self.status == AnalysisStatus.SUCCESS and self.error is not None:
            raise ValueError(
                "Successful analysis cannot contain an error"
            )

        if self.status != AnalysisStatus.SUCCESS:
            if self.error is None:
                raise ValueError(
                    "Failed analysis requires an error"
                )

        return self


# ============================================================================
# FIELD COMPARISON
# ============================================================================
class FieldComparison(BaseModel):
    """Comparación de un campo entre Gemini y Ollama."""

    field: ComparisonField

    gemini_value: str | float | int | None

    ollama_value: str | float | int | None

    agreement: AgreementLevel


# ============================================================================
# COMPARISON
# ============================================================================


class Comparison(BaseModel):
    """Comparación estructurada entre Gemini y Ollama."""

    status: ComparisonStatus

    fields: list[FieldComparison] = Field(
        default_factory=list,
    )

    strategic_agreement: AgreementLevel | None = None

    confidence_difference: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
    )

    target_lap_difference: int | None = Field(
        default=None,
        ge=0,
    )

    @model_validator(mode="after")
    def validate_comparison(self):
        if self.status == ComparisonStatus.COMPLETED:

            if not self.fields:
                raise ValueError(
                    "Completed comparison requires field comparisons"
                )

            if self.strategic_agreement is None:
                raise ValueError(
                    "Completed comparison requires strategic agreement"
                )

        if (
            self.status == ComparisonStatus.INSUFFICIENT_DATA
            and self.strategic_agreement is not None
        ):
            raise ValueError(
                "Insufficient comparison cannot have strategic agreement"
            )

        return self


# ============================================================================
# RISK FACTOR
# ============================================================================


class RiskFactor(BaseModel):
    """Factor individual que contribuye al Risk Score de ARXIA."""

    type: RiskFactorType

    score: int = Field(
        ge=0,
        le=100,
    )

    severity: RiskLevel

    description: str = Field(
        min_length=1,
    )

    @field_validator("description")
    @classmethod
    def normalize_description(cls, value: str) -> str:
        value = " ".join(value.split())

        if not value:
            raise ValueError(
                "Risk factor description cannot be empty"
            )

        return value


# ============================================================================
# RISK ASSESSMENT
# ============================================================================


class RiskAssessment(BaseModel):
    """Evaluación determinista del riesgo de automatización."""

    risk_score: int = Field(
        ge=0,
        le=100,
    )

    risk_level: RiskLevel

    risk_factors: list[RiskFactor] = Field(
        default_factory=list,
    )

    explanation: str = Field(
        min_length=1,
    )

    @field_validator("explanation")
    @classmethod
    def normalize_explanation(cls, value: str) -> str:
        value = " ".join(value.split())

        if not value:
            raise ValueError(
                "Risk explanation cannot be empty"
            )

        return value

    @model_validator(mode="after")
    def validate_risk_level(self):
        if self.risk_score <= 24:
            expected_level = RiskLevel.LOW

        elif self.risk_score <= 49:
            expected_level = RiskLevel.MEDIUM

        elif self.risk_score <= 74:
            expected_level = RiskLevel.HIGH

        else:
            expected_level = RiskLevel.CRITICAL

        if self.risk_level != expected_level:
            raise ValueError(
                "Risk level does not match risk score"
            )

        return self


# ============================================================================
# ARXIA DECISION
# ============================================================================


class ArxiaDecision(BaseModel):
    """Decisión final tomada por ARXIA."""

    action: RecommendationAction

    target_lap: int | None = Field(
        default=None,
        ge=1,
    )

    tyre_compound: TyreCompound | None = None

    confidence: float = Field(
        ge=0.0,
        le=1.0,
    )

    decision: DecisionType

    risk_level: RiskLevel

    reason: DecisionReason

    supporting_models: list[Provider] = Field(
        default_factory=list,
    )

    rationale: str = Field(
        min_length=1,
    )

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
    )

    @field_validator("rationale")
    @classmethod
    def normalize_rationale(cls, value: str) -> str:
        value = " ".join(value.split())

        if not value:
            raise ValueError(
                "Decision rationale cannot be empty"
            )

        return value

    @model_validator(mode="after")
    def validate_decision(self):
        if (
            self.decision == DecisionType.AUTOMATIC
            and self.risk_level in (
                RiskLevel.HIGH,
                RiskLevel.CRITICAL,
            )
        ):
            raise ValueError(
                "High or critical risk cannot result in automatic decision"
            )

        if (
            self.decision == DecisionType.HUMAN_REVIEW
            and self.risk_level == RiskLevel.LOW
        ):
            raise ValueError(
                "Low risk should not require human review"
            )

        return self


# ============================================================================
# HUMAN REVIEW
# ============================================================================


class HumanReview(BaseModel):
    """Intervención de un ingeniero cuando ARXIA requiere revisión."""

    id: UUID = Field(
        default_factory=uuid4,
    )

    status: ReviewStatus

    final_decision: Recommendation | None = None

    reviewer_comment: str | None = None

    reviewed_at: datetime | None = None

    @field_validator("reviewer_comment")
    @classmethod
    def normalize_comment(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        value = " ".join(value.split())

        return value or None

    @model_validator(mode="after")
    def validate_review(self):
        if self.status == ReviewStatus.PENDING:

            if self.final_decision is not None:
                raise ValueError(
                    "Pending review cannot have final decision"
                )

            if self.reviewed_at is not None:
                raise ValueError(
                    "Pending review cannot have reviewed_at"
                )

        else:

            if self.final_decision is None:
                raise ValueError(
                    "Completed review requires final decision"
                )

            if self.reviewed_at is None:
                raise ValueError(
                    "Completed review requires reviewed_at"
                )

        return self


# ============================================================================
# ARXIA RESULT
# ============================================================================


class ArxiaResult(BaseModel):
    """Resultado completo de una ejecución de ARXIA."""

    id: UUID = Field(
        default_factory=uuid4,
    )

    race_event: RaceEvent

    gemini_analysis: AIAnalysis

    ollama_analysis: AIAnalysis

    comparison: Comparison

    risk_assessment: RiskAssessment

    decision: ArxiaDecision

    human_review: HumanReview | None = None

    processed_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
    )

    @model_validator(mode="after")
    def validate_result(self):
        if self.gemini_analysis.provider != Provider.GEMINI:
            raise ValueError(
                "gemini_analysis must use GEMINI provider"
            )

        if self.ollama_analysis.provider != Provider.OLLAMA:
            raise ValueError(
                "ollama_analysis must use OLLAMA provider"
            )

        if (
            self.decision.decision == DecisionType.AUTOMATIC
            and self.human_review is not None
        ):
            raise ValueError(
                "Automatic decision cannot have human review"
            )

        if (
            self.decision.decision == DecisionType.HUMAN_REVIEW
            and self.human_review is None
        ):
            raise ValueError(
                "Human review decision requires human review"
            )

        return self