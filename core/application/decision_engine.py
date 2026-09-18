"""
Motor de decisión de ARXIA.

Transforma los análisis de Gemini y Ollama, junto con su comparación
y evaluación de riesgo, en una decisión automática o una solicitud
de revisión humana.

El motor es determinista y no depende de ningún proveedor de IA.
"""

from core.domain.enums import (
    AnalysisStatus,
    DecisionReason,
    DecisionType,
    Provider,
    RecommendationAction,
    RiskLevel,
)
from core.domain.schemas import (
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
        """Inicializa el motor con el umbral mínimo de confianza."""

        if not 0.0 <= confidence_threshold <= 1.0:
            raise ValueError(
                "Confidence threshold must be between 0 and 1"
            )

        self.confidence_threshold = confidence_threshold

    # ==================================================================
    # DECISIÓN PRINCIPAL
    # ==================================================================

    def decide(
        self,
        gemini_analysis: AIAnalysis,
        ollama_analysis: AIAnalysis,
        comparison: Comparison,
        risk_assessment: RiskAssessment,
    ) -> ArxiaDecision:
        """
        Genera la decisión final de ARXIA.

        La automatización solo está permitida cuando:

        - ambos proveedores son válidos;
        - ambos análisis terminaron correctamente;
        - la comparación está completada;
        - existe acuerdo estratégico;
        - las recomendaciones son suficientemente confiables;
        - el riesgo final es LOW.

        Cualquier otra situación requiere revisión humana.
        """

        # --------------------------------------------------------------
        # 1. VALIDACIÓN DE PROVEEDORES
        # --------------------------------------------------------------

        if not self._both_models_succeeded(
            gemini_analysis,
            ollama_analysis,
        ):
            return self._human_review_decision(
                risk_level=self._review_risk(
                    risk_assessment.risk_level,
                    RiskLevel.HIGH,
                ),
                reason=DecisionReason.PROVIDER_FAILURE,
                gemini_analysis=gemini_analysis,
                ollama_analysis=ollama_analysis,
            )

        # --------------------------------------------------------------
        # 2. RIESGO NO AUTOMATIZABLE
        # --------------------------------------------------------------

        if risk_assessment.risk_level in (
            RiskLevel.CRITICAL,
            RiskLevel.HIGH,
            RiskLevel.MEDIUM,
        ):
            return self._human_review_decision(
                risk_level=risk_assessment.risk_level,
                reason=self._risk_reason(
                    risk_assessment.risk_level
                ),
                gemini_analysis=gemini_analysis,
                ollama_analysis=ollama_analysis,
            )

        # --------------------------------------------------------------
        # 3. COMPARACIÓN
        # --------------------------------------------------------------

        if not self._comparison_supports_automation(
            comparison
        ):
            return self._human_review_decision(
                risk_level=self._review_risk(
                    risk_assessment.risk_level,
                    RiskLevel.MEDIUM,
                ),
                reason=DecisionReason.MODEL_DISAGREEMENT,
                gemini_analysis=gemini_analysis,
                ollama_analysis=ollama_analysis,
            )

        # --------------------------------------------------------------
        # 4. CONFIANZA
        # --------------------------------------------------------------

        if not self._confidence_is_sufficient(
            gemini_analysis,
            ollama_analysis,
        ):
            return self._human_review_decision(
                risk_level=self._review_risk(
                    risk_assessment.risk_level,
                    RiskLevel.MEDIUM,
                ),
                reason=DecisionReason.LOW_CONFIDENCE,
                gemini_analysis=gemini_analysis,
                ollama_analysis=ollama_analysis,
            )

        # --------------------------------------------------------------
        # 5. ACUERDO ESTRATÉGICO
        # --------------------------------------------------------------

        if not self._strategic_agreement_supports_automation(
            comparison
        ):
            return self._human_review_decision(
                risk_level=self._review_risk(
                    risk_assessment.risk_level,
                    RiskLevel.MEDIUM,
                ),
                reason=DecisionReason.MODEL_DISAGREEMENT,
                gemini_analysis=gemini_analysis,
                ollama_analysis=ollama_analysis,
            )

        # --------------------------------------------------------------
        # 6. AUTOMATIZACIÓN
        # --------------------------------------------------------------

        return self._automatic_decision(
            gemini_analysis=gemini_analysis,
            ollama_analysis=ollama_analysis,
        )

    # ==================================================================
    # VALIDACIONES
    # ==================================================================

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
    def _strategic_agreement_supports_automation(
        comparison: Comparison,
    ) -> bool:
        """Comprueba que existe acuerdo estratégico explícito."""

        return (
            comparison.strategic_agreement is not None
            and comparison.strategic_agreement.value == "agree"
        )

    @staticmethod
    def _comparison_supports_automation(
        comparison: Comparison,
    ) -> bool:
        """
        Comprueba que la comparación está completamente disponible.

        Una comparación incompleta requiere revisión humana.
        """

        return comparison.status.value == "completed"

    def _confidence_is_sufficient(
        self,
        gemini_analysis: AIAnalysis,
        ollama_analysis: AIAnalysis,
    ) -> bool:
        """Comprueba la confianza mínima de ambos modelos."""

        return (
            gemini_analysis.confidence
            >= self.confidence_threshold
            and ollama_analysis.confidence
            >= self.confidence_threshold
            and gemini_analysis.recommendation.confidence
            >= self.confidence_threshold
            and ollama_analysis.recommendation.confidence
            >= self.confidence_threshold
        )

    # ==================================================================
    # HELPERS DE RIESGO
    # ==================================================================

    @staticmethod
    def _review_risk(
        current_risk: RiskLevel,
        minimum_risk: RiskLevel,
    ) -> RiskLevel:
        """
        Garantiza que una revisión humana nunca se represente con
        un nivel de riesgo inferior al mínimo indicado.
        """

        order = {
            RiskLevel.LOW: 0,
            RiskLevel.MEDIUM: 1,
            RiskLevel.HIGH: 2,
            RiskLevel.CRITICAL: 3,
        }

        if order[current_risk] < order[minimum_risk]:
            return minimum_risk

        return current_risk

    @staticmethod
    def _risk_reason(
        risk_level: RiskLevel,
    ) -> DecisionReason:
        """Convierte el nivel de riesgo en la razón correspondiente."""

        if risk_level == RiskLevel.CRITICAL:
            return DecisionReason.CRITICAL_RISK

        if risk_level == RiskLevel.HIGH:
            return DecisionReason.HIGH_RISK

        return DecisionReason.INSUFFICIENT_INFORMATION

    # ==================================================================
    # SELECCIÓN DE RECOMENDACIÓN
    # ==================================================================

    @staticmethod
    def _select_action(
        gemini_analysis: AIAnalysis,
        ollama_analysis: AIAnalysis,
    ) -> RecommendationAction:
        """Selecciona la acción únicamente cuando ambos coinciden."""

        gemini_action = gemini_analysis.recommendation.action
        ollama_action = ollama_analysis.recommendation.action

        if gemini_action == ollama_action:
            return gemini_action

        return RecommendationAction.NO_ACTION

    @staticmethod
    def _select_target_lap(
        gemini_analysis: AIAnalysis,
        ollama_analysis: AIAnalysis,
    ) -> int | None:
        """
        Selecciona la vuelta objetivo.

        Si ambos modelos indican una vuelta, deben coincidir para
        automatizar. Si ambos coinciden en None, se mantiene None.
        """

        gemini_lap = gemini_analysis.recommendation.target_lap
        ollama_lap = ollama_analysis.recommendation.target_lap

        if gemini_lap == ollama_lap:
            return gemini_lap

        return None

    @staticmethod
    def _select_tyre_compound(
        gemini_analysis: AIAnalysis,
        ollama_analysis: AIAnalysis,
    ):
        """
        Selecciona el compuesto.

        Si ambos modelos proporcionan el mismo valor, se utiliza ese
        valor. Si uno de ellos no proporciona información, se utiliza
        el valor disponible del otro modelo.

        Si ambos proporcionan valores diferentes, no se selecciona
        ningún compuesto automáticamente.
        """

        gemini_compound = gemini_analysis.recommendation.tyre_compound
        ollama_compound = ollama_analysis.recommendation.tyre_compound

        if (
            gemini_compound is not None
            and ollama_compound is not None
        ):
            if gemini_compound == ollama_compound:
                return gemini_compound

            return None

        if gemini_compound is not None:
            return gemini_compound

        if ollama_compound is not None:
            return ollama_compound

        return None

    @staticmethod
    def _combined_confidence(
        gemini_analysis: AIAnalysis,
        ollama_analysis: AIAnalysis,
    ) -> float:
        """Calcula una confianza conservadora."""

        return min(
            gemini_analysis.confidence,
            ollama_analysis.confidence,
            gemini_analysis.recommendation.confidence,
            ollama_analysis.recommendation.confidence,
        )

    # ==================================================================
    # DECISIÓN AUTOMÁTICA
    # ==================================================================

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

    # ==================================================================
    # REVISIÓN HUMANA
    # ==================================================================

    @staticmethod
    def _human_review_decision(
        risk_level: RiskLevel,
        reason: DecisionReason,
        gemini_analysis: AIAnalysis,
        ollama_analysis: AIAnalysis,
    ) -> ArxiaDecision:
        """
        Construye una decisión de revisión humana.

        La recomendación de un modelo válido se presenta únicamente
        como propuesta para el revisor.
        """

        gemini_valid = (
            gemini_analysis.provider == Provider.GEMINI
            and gemini_analysis.status == AnalysisStatus.SUCCESS
        )

        ollama_valid = (
            ollama_analysis.provider == Provider.OLLAMA
            and ollama_analysis.status == AnalysisStatus.SUCCESS
        )

        # --------------------------------------------------------------
        # RECOMENDACIÓN DE REFERENCIA
        # --------------------------------------------------------------

        if gemini_valid:
            recommendation = gemini_analysis.recommendation

        elif ollama_valid:
            recommendation = ollama_analysis.recommendation

        else:
            recommendation = gemini_analysis.recommendation

        # --------------------------------------------------------------
        # MODELOS VÁLIDOS
        # --------------------------------------------------------------

        successful_analyses = [
            analysis
            for analysis in (
                gemini_analysis,
                ollama_analysis,
            )
            if (
                analysis.status == AnalysisStatus.SUCCESS
                and analysis.provider in (
                    Provider.GEMINI,
                    Provider.OLLAMA,
                )
            )
        ]

        # --------------------------------------------------------------
        # CONFIANZA
        # --------------------------------------------------------------

        successful_confidences = [
            analysis.confidence
            for analysis in successful_analyses
        ]

        confidence = (
            min(successful_confidences)
            if successful_confidences
            else 0.0
        )

        # --------------------------------------------------------------
        # MODELOS DE APOYO
        # --------------------------------------------------------------

        supporting_models = [
            analysis.provider
            for analysis in successful_analyses
        ]

        # --------------------------------------------------------------
        # RESULTADO
        # --------------------------------------------------------------

        return ArxiaDecision(
            action=recommendation.action,
            target_lap=recommendation.target_lap,
            tyre_compound=recommendation.tyre_compound,
            confidence=confidence,
            decision=DecisionType.HUMAN_REVIEW,
            risk_level=risk_level,
            reason=reason,
            supporting_models=supporting_models,
            rationale=(
                "ARXIA requires human review because the current "
                "analysis does not satisfy the conditions for safe "
                "automatic decision-making. The available valid model "
                "recommendation is provided only as a proposal for "
                "human review."
            ),
        )