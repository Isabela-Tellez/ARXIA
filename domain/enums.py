"""
Enums del dominio de ARXIA.

Definen los valores controlados utilizados por el motor de decisión
multimodelo de motorsport.
"""

from enum import Enum


# ============================================================================
# RACE EVENT
# ============================================================================


class RaceSession(str, Enum):
    """Sesión de motorsport en la que ocurre el evento."""

    PRACTICE = "practice"
    QUALIFYING = "qualifying"
    SPRINT = "sprint"
    RACE = "race"


class EventType(str, Enum):
    """Tipo de evento de carrera analizado por ARXIA."""

    TYRE_DEGRADATION = "tyre_degradation"
    PIT_WINDOW = "pit_window"
    WEATHER_CHANGE = "weather_change"
    MECHANICAL_ISSUE = "mechanical_issue"
    TRACK_CHANGE = "track_change"
    SAFETY_CAR = "safety_car"
    VIRTUAL_SAFETY_CAR = "virtual_safety_car"
    RACE_INCIDENT = "race_incident"
    STRATEGIC_OPPORTUNITY = "strategic_opportunity"
    OTHER = "other"


class WeatherCondition(str, Enum):
    """Condición meteorológica o de pista."""

    DRY = "dry"
    DAMP = "damp"
    WET = "wet"
    RAIN = "rain"
    STORM = "storm"
    UNKNOWN = "unknown"


# ============================================================================
# AI ANALYSIS
# ============================================================================


class AnalysisCategory(str, Enum):
    """Categoría principal del análisis realizado por un modelo."""

    TYRE_STRATEGY = "tyre_strategy"
    RACE_STRATEGY = "race_strategy"
    WEATHER = "weather"
    MECHANICAL = "mechanical"
    SAFETY = "safety"
    POSITION = "position"
    OTHER = "other"


class AnalysisUrgency(str, Enum):
    """Urgencia operativa identificada por un modelo."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Provider(str, Enum):
    """Proveedor de IA utilizado para realizar el análisis."""

    GEMINI = "gemini"
    OLLAMA = "ollama"


class AnalysisStatus(str, Enum):
    """Estado técnico de una ejecución de análisis."""

    SUCCESS = "success"
    INVALID = "invalid"
    TIMEOUT = "timeout"
    ERROR = "error"


# ============================================================================
# RECOMMENDATION
# ============================================================================


class RecommendationAction(str, Enum):
    """Acción estratégica propuesta por un modelo."""

    PIT_STOP = "pit_stop"
    STAY_OUT = "stay_out"
    PUSH = "push"
    MANAGE_TYRES = "manage_tyres"
    DEFEND = "defend"
    ATTACK = "attack"
    NO_ACTION = "no_action"


class TyreCompound(str, Enum):
    """Compuesto de neumático asociado a una recomendación."""

    SOFT = "soft"
    MEDIUM = "medium"
    HARD = "hard"
    INTERMEDIATE = "intermediate"
    WET = "wet"


# ============================================================================
# COMPARISON
# ============================================================================


class ComparisonStatus(str, Enum):
    """Estado de la comparación entre los análisis de los modelos."""

    PENDING = "pending"
    COMPLETED = "completed"
    INSUFFICIENT_DATA = "insufficient_data"


class ComparisonField(str, Enum):
    """Campo de AIAnalysis utilizado en la comparación."""

    CATEGORY = "category"
    URGENCY = "urgency"
    ACTION = "action"
    TARGET_LAP = "target_lap"
    TYRE_COMPOUND = "tyre_compound"
    CONFIDENCE = "confidence"


class AgreementLevel(str, Enum):
    """Nivel de acuerdo entre los modelos para un campo."""

    AGREE = "agree"
    CLOSE = "close"
    DISAGREE = "disagree"
    NOT_COMPARABLE = "not_comparable"


# ============================================================================
# RISK ASSESSMENT
# ============================================================================


class RiskLevel(str, Enum):
    """Nivel de riesgo asociado a automatizar una decisión."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RiskFactorType(str, Enum):
    """Factor que contribuye al riesgo de automatización."""

    MODEL_DISAGREEMENT = "model_disagreement"
    LOW_CONFIDENCE = "low_confidence"
    CONFIDENCE_GAP = "confidence_gap"
    EVENT_CRITICALITY = "event_criticality"
    TIMING_DISAGREEMENT = "timing_disagreement"
    PROVIDER_FAILURE = "provider_failure"
    INSUFFICIENT_INFORMATION = "insufficient_information"


# ============================================================================
# ARXIA DECISION
# ============================================================================


class DecisionType(str, Enum):
    """Tipo de decisión final tomada por ARXIA."""

    AUTOMATIC = "automatic"
    HUMAN_REVIEW = "human_review"


class DecisionReason(str, Enum):
    """Motivo principal que explica la decisión de ARXIA."""

    MODELS_AGREE = "models_agree"
    LOW_RISK = "low_risk"
    MODEL_DISAGREEMENT = "model_disagreement"
    HIGH_RISK = "high_risk"
    CRITICAL_RISK = "critical_risk"
    LOW_CONFIDENCE = "low_confidence"
    PROVIDER_FAILURE = "provider_failure"
    INSUFFICIENT_INFORMATION = "insufficient_information"


# ============================================================================
# HUMAN REVIEW
# ============================================================================


class ReviewStatus(str, Enum):
    """Estado actual de una revisión humana."""

    PENDING = "pending"
    ACCEPTED = "accepted"
    CORRECTED = "corrected"