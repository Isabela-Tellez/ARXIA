"""
Motor determinista de evaluación de riesgo de ARXIA.

Transforma los resultados de los modelos y su comparación en un
RiskAssessment.

No depende de ningún proveedor de IA.
"""

from core.domain.enums import (
    AgreementLevel,
    AnalysisStatus,
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

    # ==================================================================
    # EVALUACIÓN PRINCIPAL
    # ==================================================================

    def assess(
        self,
        race_event: RaceEvent,
        gemini_analysis: AIAnalysis,
        ollama_analysis: AIAnalysis,
        comparison: Comparison,
    ) -> RiskAssessment:
        """
        Evalúa el riesgo de automatizar la decisión.

        Reglas:

        - Un proveedor fallido añade 40 puntos.
        - Un proveedor fallido no se cuenta como baja confianza.
        - La confianza de proveedores fallidos no participa en el
          cálculo de confidence gap.
        - Una comparación incompleta añade 20 puntos.
        - Un desacuerdo estratégico añade 25 puntos.
        - Una diferencia de confianza superior al umbral añade 10 puntos.
        - Un desacuerdo de vuelta añade 10 puntos.
        - Un evento crítico añade 20 puntos.
        - El score máximo es 100.
        - El nivel siempre se calcula a partir del score.
        - Un fallo de proveedor garantiza como mínimo HIGH.
        - No se fuerza CRITICAL únicamente por la combinación de
          fallo de proveedor e información insuficiente.
        """

        factors: list[RiskFactor] = []

        # --------------------------------------------------------------
        # 1. FALLO DE PROVEEDOR
        # --------------------------------------------------------------

        provider_failure = self._add_provider_failure_factor(
            factors,
            gemini_analysis,
            ollama_analysis,
        )

        # --------------------------------------------------------------
        # 2. DESACUERDO ESTRATÉGICO
        # --------------------------------------------------------------

        strategic_disagreement = (
            self._add_model_disagreement_factor(
                factors,
                comparison,
            )
        )

        # --------------------------------------------------------------
        # 3. BAJA CONFIANZA
        # --------------------------------------------------------------

        self._add_low_confidence_factor(
            factors,
            gemini_analysis,
            ollama_analysis,
        )

        # --------------------------------------------------------------
        # 4. DIFERENCIA DE CONFIANZA
        # --------------------------------------------------------------

        self._add_confidence_gap_factor(
            factors,
            gemini_analysis,
            ollama_analysis,
        )

        # --------------------------------------------------------------
        # 5. DESACUERDO TEMPORAL
        # --------------------------------------------------------------

        self._add_timing_disagreement_factor(
            factors,
            comparison,
        )

        # --------------------------------------------------------------
        # 6. CRITICIDAD DEL EVENTO
        # --------------------------------------------------------------

        self._add_event_criticality_factor(
            factors,
            race_event,
        )

        # --------------------------------------------------------------
        # 7. INFORMACIÓN INSUFICIENTE
        # --------------------------------------------------------------

        self._add_insufficient_information_factor(
            factors,
            comparison,
        )

        # --------------------------------------------------------------
        # SCORE
        # --------------------------------------------------------------

        risk_score = min(
            100,
            sum(
                factor.score
                for factor in factors
            ),
        )

        risk_level = self._risk_level_from_score(
            risk_score,
        )

        # --------------------------------------------------------------
        # GARANTÍA DE SEGURIDAD PARA FALLO DE PROVEEDOR
        # --------------------------------------------------------------

        if provider_failure:
            # Un fallo de proveedor no puede considerarse LOW
            # ni MEDIUM.
            #
            # Importante:
            # No convertimos automáticamente provider failure +
            # insufficient information en CRITICAL.
            #
            # Ejemplo:
            # provider failure = 40
            # insufficient information = 20
            # total = 60 -> HIGH
            #
            # Esto mantiene el score determinista y coherente
            # con los factores realmente detectados.

            risk_score = max(
                risk_score,
                50,
            )

            risk_level = self._risk_level_from_score(
                risk_score,
            )

        # --------------------------------------------------------------
        # GARANTÍA DE SEGURIDAD PARA DESACUERDO ESTRATÉGICO
        # --------------------------------------------------------------

        elif strategic_disagreement:
            """
            Un desacuerdo estratégico nunca permite LOW.

            Si el score natural ya es HIGH o CRITICAL, se conserva.
            """

            risk_score = max(
                risk_score,
                25,
            )

            risk_level = self._risk_level_from_score(
                risk_score,
            )

        # --------------------------------------------------------------
        # NIVEL FINAL
        # --------------------------------------------------------------

        else:
            risk_level = self._risk_level_from_score(
                risk_score,
            )

        # --------------------------------------------------------------
        # EXPLICACIÓN
        # --------------------------------------------------------------

        explanation = self._build_explanation(
            risk_score,
            risk_level,
            factors,
        )

        # --------------------------------------------------------------
        # RESULTADO
        # --------------------------------------------------------------

        return RiskAssessment(
            risk_score=risk_score,
            risk_level=risk_level,
            risk_factors=factors,
            explanation=explanation,
        )

    # ==================================================================
    # RISK FACTORS
    # ==================================================================

    @staticmethod
    def _add_provider_failure_factor(
        factors: list[RiskFactor],
        gemini_analysis: AIAnalysis,
        ollama_analysis: AIAnalysis,
    ) -> bool:
        """
        Añade riesgo cuando uno o ambos proveedores fallan.

        Un fallo de proveedor genera un único factor de riesgo,
        independientemente de cuántos proveedores fallen.
        """

        failed_providers = []

        if gemini_analysis.status != AnalysisStatus.SUCCESS:
            failed_providers.append("Gemini")

        if ollama_analysis.status != AnalysisStatus.SUCCESS:
            failed_providers.append("Ollama")

        if not failed_providers:
            return False

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

        return True

    @staticmethod
    def _add_model_disagreement_factor(
        factors: list[RiskFactor],
        comparison: Comparison,
    ) -> bool:
        """
        Añade riesgo cuando existe desacuerdo estratégico.

        Devuelve True si existe desacuerdo estratégico real.
        """

        if comparison.status != ComparisonStatus.COMPLETED:
            return False

        if (
            comparison.strategic_agreement
            != AgreementLevel.DISAGREE
        ):
            return False

        factors.append(
            RiskFactor(
                type=RiskFactorType.MODEL_DISAGREEMENT,
                score=25,
                severity=RiskLevel.HIGH,
                description=(
                    "The models disagree on the strategic "
                    "recommendation."
                ),
            )
        )

        return True

    def _add_low_confidence_factor(
        self,
        factors: list[RiskFactor],
        gemini_analysis: AIAnalysis,
        ollama_analysis: AIAnalysis,
    ) -> None:
        """
        Añade riesgo cuando un modelo válido tiene baja confianza.

        Los proveedores que han fallado no se consideran para
        este factor.
        """

        low_confidence_providers = []

        if (
            gemini_analysis.status == AnalysisStatus.SUCCESS
            and gemini_analysis.confidence
            < self.confidence_threshold
        ):
            low_confidence_providers.append("Gemini")

        if (
            ollama_analysis.status == AnalysisStatus.SUCCESS
            and ollama_analysis.confidence
            < self.confidence_threshold
        ):
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
        entre las confianzas de ambos modelos.

        Solo se calcula cuando ambos proveedores han respondido
        correctamente.
        """

        if (
            gemini_analysis.status != AnalysisStatus.SUCCESS
            or ollama_analysis.status != AnalysisStatus.SUCCESS
        ):
            return

        confidence_gap = abs(
            gemini_analysis.confidence
            - ollama_analysis.confidence
        )

        if confidence_gap <= self.CONFIDENCE_GAP_THRESHOLD:
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
        """
        Añade riesgo cuando existe desacuerdo en la vuelta objetivo.

        Solo se evalúa cuando la comparación está completada y
        existe una diferencia de vuelta.
        """

        if comparison.status != ComparisonStatus.COMPLETED:
            return

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
                    "The race event is considered operationally "
                    "critical."
                ),
            )
        )

    @staticmethod
    def _add_insufficient_information_factor(
        factors: list[RiskFactor],
        comparison: Comparison,
    ) -> None:
        """Añade riesgo cuando no existe información suficiente."""

        if comparison.status not in (
            ComparisonStatus.INSUFFICIENT_DATA,
            ComparisonStatus.PENDING,
        ):
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

    # ==================================================================
    # HELPERS
    # ==================================================================

    @staticmethod
    def _risk_level_from_score(
        risk_score: int,
    ) -> RiskLevel:
        """
        Convierte un score numérico en nivel de riesgo.

        Rangos:

        0-24   -> LOW
        25-49  -> MEDIUM
        50-74  -> HIGH
        75-100 -> CRITICAL
        """

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