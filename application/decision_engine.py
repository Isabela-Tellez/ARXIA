"""
Motor de decisión de ARXIA.

Transforma los análisis de Gemini y Ollama, junto con su comparación
y evaluación de riesgo, en una decisión automática o una solicitud
de revisión humana.

El motor es determinista y no depende de ningún proveedor de IA.
"""

from domain.enums import (
    AnalysisStatus,
    DecisionReason,
    DecisionType,
    Provider,
    RecommendationAction,
    RiskLevel,
)
from domain.schemas import (
    AIAnalysis,
    ArxiaDecision,
    Comparison,
    RiskAssessment,
)


class DecisionEngine:
    """Determina si ARXIA puede automatizar una decisión."""

    DEFAULT_CONFIDENCE_THRESHOLD = 0.80

    def __init__(
        self,
        confidence_threshold: float = DEFAULT_CONFIDENCE_THRESHOLD,
    ):
        """
        Inicializa el motor con el umbral mínimo de confianza.

        Args:
            confidence_threshold:
                Confianza mínima requerida por cada modelo
                para permitir una decisión automática.
        """

        if not 0.0 <= confidence_threshold <= 1.0:
            raise ValueError(
                "Confidence threshold must be between 0 and 1"
            )

        self.confidence_threshold = confidence_threshold

    def decide(
        self,
        gemini_analysis: AIAnalysis,
        ollama_analysis: AIAnalysis,
        comparison: Comparison,
        risk_assessment: RiskAssessment,
    ) -> ArxiaDecision:
        """
        Genera la decisión final de ARXIA.

        La decisión sigue un enfoque conservador:

        1. Si un proveedor falla → revisión humana.
        2. Si el riesgo es crítico → revisión humana.
        3. Si el riesgo es alto → revisión humana.
        4. Si los modelos no están suficientemente de acuerdo
           → revisión humana.
        5. Si la confianza es insuficiente → revisión humana.
        6. En cualquier otro caso → decisión automática.
        """

        # ------------------------------------------------------------------
        # Regla 1: Fallo de proveedor
        # ------------------------------------------------------------------

        if not self._both_models_succeeded(
            gemini_analysis,
            ollama_analysis,
        ):
            return self._human_review_decision(
                risk_level=RiskLevel.HIGH,
                reason=DecisionReason.PROVIDER_FAILURE,
                gemini_analysis=gemini_analysis,
                ollama_analysis=ollama_analysis,
            )

        # ------------------------------------------------------------------
        # Regla 2: Riesgo crítico
        # ------------------------------------------------------------------

        if risk_assessment.risk_level == RiskLevel.CRITICAL:
            return self._human_review_decision(
                risk_level=RiskLevel.CRITICAL,
                reason=DecisionReason.CRITICAL_RISK,
                gemini_analysis=gemini_analysis,
                ollama_analysis=ollama_analysis,
            )

        # ------------------------------------------------------------------
        # Regla 3: Riesgo alto
        # ------------------------------------------------------------------

        if risk_assessment.risk_level == RiskLevel.HIGH:
            return self._human_review_decision(
                risk_level=RiskLevel.HIGH,
                reason=DecisionReason.HIGH_RISK,
                gemini_analysis=gemini_analysis,
                ollama_analysis=ollama_analysis,
            )

        # ------------------------------------------------------------------
        # Regla 4: Comparación insuficiente o desacuerdo
        # ------------------------------------------------------------------

        if not self._comparison_supports_automation(comparison):
            return self._human_review_decision(
                risk_level=self._safe_review_risk(
                    risk_assessment.risk_level
                ),
                reason=DecisionReason.MODEL_DISAGREEMENT,
                gemini_analysis=gemini_analysis,
                ollama_analysis=ollama_analysis,
            )

        # ------------------------------------------------------------------
        # Regla 5: Confianza insuficiente
        # ------------------------------------------------------------------

        if not self._confidence_is_sufficient(
            gemini_analysis,
            ollama_analysis,
        ):
            return self._human_review_decision(
                risk_level=RiskLevel.MEDIUM,
                reason=DecisionReason.LOW_CONFIDENCE,
                gemini_analysis=gemini_analysis,
                ollama_analysis=ollama_analysis,
            )

        # ------------------------------------------------------------------
        # Regla 6: Información insuficiente
        # ------------------------------------------------------------------

        if risk_assessment.risk_level == RiskLevel.MEDIUM:
            return self._human_review_decision(
                risk_level=RiskLevel.MEDIUM,
                reason=DecisionReason.INSUFFICIENT_INFORMATION,
                gemini_analysis=gemini_analysis,
                ollama_analysis=ollama_analysis,
            )

        # ------------------------------------------------------------------
        # Regla 7: Modelos alineados + bajo riesgo
        # ------------------------------------------------------------------

        return self._automatic_decision(
            gemini_analysis=gemini_analysis,
            ollama_analysis=ollama_analysis,
        )

    # ======================================================================
    # VALIDACIONES
    # ======================================================================

    @staticmethod
    def _both_models_succeeded(
        gemini_analysis: AIAnalysis,
        ollama_analysis: AIAnalysis,
    ) -> bool:
        """Comprueba que ambos proveedores terminaron correctamente."""

        return (
            gemini_analysis.provider == Provider.GEMINI
            and ollama_analysis.provider == Provider.OLLAMA
            and gemini_analysis.status == AnalysisStatus.SUCCESS
            and ollama_analysis.status == AnalysisStatus.SUCCESS
        )

    @staticmethod
    def _comparison_supports_automation(
        comparison: Comparison,
    ) -> bool:
        """
        Determina si la comparación permite automatizar.

        Solo una comparación completada con acuerdo estratégico
        explícito puede continuar hacia una decisión automática.
        """

        return (
            comparison.status.value == "completed"
            and comparison.strategic_agreement is not None
            and comparison.strategic_agreement.value == "agree"
        )

    def _confidence_is_sufficient(
        self,
        gemini_analysis: AIAnalysis,
        ollama_analysis: AIAnalysis,
    ) -> bool:
        """Comprueba la confianza mínima de ambos modelos."""

        return (
            gemini_analysis.confidence >= self.confidence_threshold
            and ollama_analysis.confidence >= self.confidence_threshold
            and gemini_analysis.recommendation.confidence
            >= self.confidence_threshold
            and ollama_analysis.recommendation.confidence
            >= self.confidence_threshold
        )

    @staticmethod
    def _safe_review_risk(
        risk_level: RiskLevel,
    ) -> RiskLevel:
        """
        Normaliza el riesgo utilizado para una revisión humana.

        Nunca permite que un desacuerdo sea representado como LOW.
        """

        if risk_level == RiskLevel.LOW:
            return RiskLevel.MEDIUM

        return risk_level

    # ======================================================================
    # DECISIONES
    # ======================================================================

    @staticmethod
    def _select_action(
        gemini_analysis: AIAnalysis,
        ollama_analysis: AIAnalysis,
    ) -> RecommendationAction:
        """
        Selecciona la acción estratégica.

        En una situación de acuerdo, ambos modelos deberían proponer
        la misma acción. Gemini actúa como primera referencia y Ollama
        como segunda validación.
        """

        gemini_action = gemini_analysis.recommendation.action
        ollama_action = ollama_analysis.recommendation.action

        if gemini_action == ollama_action:
            return gemini_action

        # Esta situación no debería llegar a una decisión automática,
        # pero se utiliza un fallback seguro para mantener el objeto
        # ArxiaDecision válido.
        return RecommendationAction.NO_ACTION

    @staticmethod
    def _select_target_lap(
        gemini_analysis: AIAnalysis,
        ollama_analysis: AIAnalysis,
    ) -> int | None:
        """Selecciona la vuelta objetivo cuando ambos modelos coinciden."""

        gemini_lap = gemini_analysis.recommendation.target_lap
        ollama_lap = ollama_analysis.recommendation.target_lap

        if gemini_lap == ollama_lap:
            return gemini_lap

        if gemini_lap is None:
            return ollama_lap

        if ollama_lap is None:
            return gemini_lap

        return round((gemini_lap + ollama_lap) / 2)

    @staticmethod
    def _select_tyre_compound(
        gemini_analysis: AIAnalysis,
        ollama_analysis: AIAnalysis,
    ):
        """Selecciona el compuesto cuando existe acuerdo."""

        gemini_compound = (
            gemini_analysis.recommendation.tyre_compound
        )

        ollama_compound = (
            ollama_analysis.recommendation.tyre_compound
        )

        if gemini_compound == ollama_compound:
            return gemini_compound

        if gemini_compound is None:
            return ollama_compound

        if ollama_compound is None:
            return gemini_compound

        return None

    @staticmethod
    def _combined_confidence(
        gemini_analysis: AIAnalysis,
        ollama_analysis: AIAnalysis,
    ) -> float:
        """
        Calcula una confianza conservadora.

        Se utiliza la menor confianza de los dos modelos para evitar
        que un modelo muy confiado oculte la incertidumbre del otro.
        """

        return min(
            gemini_analysis.confidence,
            ollama_analysis.confidence,
            gemini_analysis.recommendation.confidence,
            ollama_analysis.recommendation.confidence,
        )

    def _automatic_decision(
        self,
        gemini_analysis: AIAnalysis,
        ollama_analysis: AIAnalysis,
    ) -> ArxiaDecision:
        """Construye una decisión automática."""

        action = self._select_action(
            gemini_analysis,
            ollama_analysis,
        )

        target_lap = self._select_target_lap(
            gemini_analysis,
            ollama_analysis,
        )

        tyre_compound = self._select_tyre_compound(
            gemini_analysis,
            ollama_analysis,
        )

        confidence = self._combined_confidence(
            gemini_analysis,
            ollama_analysis,
        )

        return ArxiaDecision(
            action=action,
            target_lap=target_lap,
            tyre_compound=tyre_compound,
            confidence=confidence,
            decision=DecisionType.AUTOMATIC,
            risk_level=RiskLevel.LOW,
            reason=DecisionReason.MODELS_AGREE,
            supporting_models=[
                Provider.GEMINI,
                Provider.OLLAMA,
            ],
            rationale=(
                "Gemini and Ollama agree on the strategic recommendation "
                "with sufficient confidence and low automation risk."
            ),
        )

    @staticmethod
    def _human_review_decision(
        risk_level: RiskLevel,
        reason: DecisionReason,
        gemini_analysis: AIAnalysis,
        ollama_analysis: AIAnalysis,
    ) -> ArxiaDecision:
        """
        Construye una decisión que requiere intervención humana.

        Para revisión humana utilizamos la recomendación de Gemini
        como propuesta inicial, pero nunca la consideramos una
        decisión automática.
        """

        recommendation = gemini_analysis.recommendation

        return ArxiaDecision(
            action=recommendation.action,
            target_lap=recommendation.target_lap,
            tyre_compound=recommendation.tyre_compound,
            confidence=min(
                gemini_analysis.confidence,
                ollama_analysis.confidence,
            ),
            decision=DecisionType.HUMAN_REVIEW,
            risk_level=risk_level,
            reason=reason,
            supporting_models=[
                Provider.GEMINI,
                Provider.OLLAMA,
            ],
            rationale=(
                "ARXIA requires human review because the current "
                "analysis does not satisfy the conditions for safe "
                "automatic decision-making."
            ),
        )