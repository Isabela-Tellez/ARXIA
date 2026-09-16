"""
Motor determinista de evaluación de riesgo de ARXIA.

Transforma los resultados de los modelos y su comparación en un
RiskAssessment. No depende de ningún proveedor de IA.
"""
import math

from core.domain.enums import (
    AnalysisStatus,
    AgreementLevel,
    ComparisonStatus,
    RiskFactorType,
    RiskLevel,
)
from core.domain.schemas import (
    AIAnalysis,
    Comparison,
    RaceEvent,
    RiskAssessment,
    RiskFactor,
)


class RiskEngine:
    """Calcula de forma determinista el riesgo de automatización."""

    DEFAULT_CONFIDENCE_THRESHOLD = 0.80
    CONFIDENCE_GAP_THRESHOLD = 0.20

    def __init__(
        self,
        confidence_threshold: float = DEFAULT_CONFIDENCE_THRESHOLD,
    ):
        if not 0.0 <= confidence_threshold <= 1.0:
            raise ValueError(
                "Confidence threshold must be between 0 and 1"
            )

        self.confidence_threshold = confidence_threshold

    def assess(
        self,
        race_event: RaceEvent,
        gemini_analysis: AIAnalysis,
        ollama_analysis: AIAnalysis,
        comparison: Comparison,
    ) -> RiskAssessment:
        """
        Evalúa el riesgo de automatizar la decisión.

        El cálculo es determinista y se basa únicamente en los datos
        estructurados producidos por el pipeline de ARXIA.
        """

        factors: list[RiskFactor] = []

        self._add_provider_failure_factor(
            factors,
            gemini_analysis,
            ollama_analysis,
        )

        self._add_model_disagreement_factor(
            factors,
            comparison,
        )

        self._add_low_confidence_factor(
            factors,
            gemini_analysis,
            ollama_analysis,
        )

        self._add_confidence_gap_factor(
            factors,
            gemini_analysis,
            ollama_analysis,
        )

        self._add_timing_disagreement_factor(
            factors,
            comparison,
        )

        self._add_event_criticality_factor(
            factors,
            race_event,
        )

        self._add_insufficient_information_factor(
            factors,
            comparison,
        )

        risk_score = min(
            100,
            sum(factor.score for factor in factors),
        )

        risk_level = self._risk_level_from_score(
            risk_score,
        )

        explanation = self._build_explanation(
            risk_score,
            risk_level,
            factors,
        )

        return RiskAssessment(
            risk_score=risk_score,
            risk_level=risk_level,
            risk_factors=factors,
            explanation=explanation,
        )

    # ======================================================================
    # RISK FACTORS
    # ======================================================================

    @staticmethod
    def _add_provider_failure_factor(
        factors: list[RiskFactor],
        gemini_analysis: AIAnalysis,
        ollama_analysis: AIAnalysis,
    ) -> None:
        """Añade riesgo cuando uno o ambos proveedores fallan."""

        failed_providers = []

        if gemini_analysis.status != AnalysisStatus.SUCCESS:
            failed_providers.append("Gemini")

        if ollama_analysis.status != AnalysisStatus.SUCCESS:
            failed_providers.append("Ollama")

        if not failed_providers:
            return

        factors.append(
            RiskFactor(
                type=RiskFactorType.PROVIDER_FAILURE,
                score=40,
                severity=RiskLevel.HIGH,
                description=(
                    "Provider failure detected: "
                    + ", ".join(failed_providers)
                    + "."
                ),
            )
        )

    @staticmethod
    def _add_model_disagreement_factor(
        factors: list[RiskFactor],
        comparison: Comparison,
    ) -> None:
        """Añade riesgo cuando los modelos no coinciden."""

        if comparison.status != ComparisonStatus.COMPLETED:
            return

        if comparison.strategic_agreement == AgreementLevel.AGREE:
            return

        factors.append(
            RiskFactor(
                type=RiskFactorType.MODEL_DISAGREEMENT,
                score=25,
                severity=RiskLevel.HIGH,
                description=(
                    "The models disagree on the strategic recommendation."
                ),
            )
        )

    def _add_low_confidence_factor(
        self,
        factors: list[RiskFactor],
        gemini_analysis: AIAnalysis,
        ollama_analysis: AIAnalysis,
    ) -> None:
        """Añade riesgo cuando la confianza de algún modelo es baja."""

        low_confidence_providers = []

        if gemini_analysis.confidence < self.confidence_threshold:
            low_confidence_providers.append("Gemini")

        if ollama_analysis.confidence < self.confidence_threshold:
            low_confidence_providers.append("Ollama")

        if not low_confidence_providers:
            return

        factors.append(
            RiskFactor(
                type=RiskFactorType.LOW_CONFIDENCE,
                score=20,
                severity=RiskLevel.MEDIUM,
                description=(
                    "Low model confidence detected for: "
                    + ", ".join(low_confidence_providers)
                    + "."
                ),
            )
        )

    def _add_confidence_gap_factor(
        self,
        factors: list[RiskFactor],
        gemini_analysis: AIAnalysis,
        ollama_analysis: AIAnalysis,
    ) -> None:
        """
        Añade riesgo cuando existe una diferencia significativa
        de confianza entre los modelos.

        Una diferencia exactamente igual al umbral no se considera
        un gap significativo. Se utiliza una comparación tolerante
        para evitar errores de precisión de punto flotante.
        """

        confidence_gap = abs(
            gemini_analysis.confidence
            - ollama_analysis.confidence
        )

        if (
            confidence_gap < self.CONFIDENCE_GAP_THRESHOLD
            or math.isclose(
                confidence_gap,
                self.CONFIDENCE_GAP_THRESHOLD,
                rel_tol=1e-9,
                abs_tol=1e-9,
            )
        ):
            return

        factors.append(
            RiskFactor(
                type=RiskFactorType.CONFIDENCE_GAP,
                score=10,
                severity=RiskLevel.MEDIUM,
                description=(
                    "The confidence gap between the models is "
                    f"{confidence_gap:.2f}."
                ),
            )
        )

    @staticmethod
    def _add_timing_disagreement_factor(
        factors: list[RiskFactor],
        comparison: Comparison,
    ) -> None:
        """Añade riesgo cuando existe desacuerdo en la vuelta objetivo."""

        if comparison.target_lap_difference is None:
            return

        if comparison.target_lap_difference == 0:
            return

        factors.append(
            RiskFactor(
                type=RiskFactorType.TIMING_DISAGREEMENT,
                score=10,
                severity=RiskLevel.MEDIUM,
                description=(
                    "The models disagree on the target lap."
                ),
            )
        )

    @staticmethod
    def _add_event_criticality_factor(
        factors: list[RiskFactor],
        race_event: RaceEvent,
    ) -> None:
        """Añade riesgo para eventos inherentemente críticos."""

        critical_events = {
            "mechanical_issue",
            "safety_car",
            "virtual_safety_car",
            "race_incident",
        }

        if race_event.event_type.value not in critical_events:
            return

        factors.append(
            RiskFactor(
                type=RiskFactorType.EVENT_CRITICALITY,
                score=20,
                severity=RiskLevel.HIGH,
                description=(
                    "The race event is considered operationally critical."
                ),
            )
        )

    @staticmethod
    def _add_insufficient_information_factor(
        factors: list[RiskFactor],
        comparison: Comparison,
    ) -> None:
        """Añade riesgo cuando no existe información suficiente."""

        if comparison.status != ComparisonStatus.INSUFFICIENT_DATA:
            return

        factors.append(
            RiskFactor(
                type=RiskFactorType.INSUFFICIENT_INFORMATION,
                score=20,
                severity=RiskLevel.MEDIUM,
                description=(
                    "There is insufficient information to compare "
                    "the model analyses."
                ),
            )
        )

    # ======================================================================
    # SCORE
    # ======================================================================

    @staticmethod
    def _risk_level_from_score(
        risk_score: int,
    ) -> RiskLevel:
        """Convierte un score numérico en un nivel de riesgo."""

        if risk_score <= 24:
            return RiskLevel.LOW

        if risk_score <= 49:
            return RiskLevel.MEDIUM

        if risk_score <= 74:
            return RiskLevel.HIGH

        return RiskLevel.CRITICAL

    @staticmethod
    def _build_explanation(
        risk_score: int,
        risk_level: RiskLevel,
        factors: list[RiskFactor],
    ) -> str:
        """Genera una explicación determinista del riesgo."""

        if not factors:
            return (
                "No significant automation risk factors were detected."
            )

        factor_count = len(factors)

        return (
            f"Automation risk is {risk_level.value} with a score of "
            f"{risk_score}/100 based on {factor_count} risk factor(s)."
        )