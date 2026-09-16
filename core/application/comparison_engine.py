"""
Motor determinista de comparación de ARXIA.

Compara los análisis producidos por Gemini y Ollama y genera
un objeto Comparison. No depende de ningún proveedor de IA.
"""

from core.domain.enums import (
    AgreementLevel,
    AnalysisStatus,
    ComparisonField,
    ComparisonStatus,
)
from core.domain.schemas import (
    AIAnalysis,
    Comparison,
    FieldComparison,
)


class ComparisonEngine:
    """Compara de forma determinista dos análisis de IA."""

    def compare(
        self,
        gemini_analysis: AIAnalysis,
        ollama_analysis: AIAnalysis,
    ) -> Comparison:
        """
        Compara los análisis de Gemini y Ollama.

        Si alguno de los análisis no terminó correctamente,
        la comparación se considera insuficiente.
        """

        if not self._analyses_are_comparable(
            gemini_analysis,
            ollama_analysis,
        ):
            return Comparison(
                status=ComparisonStatus.INSUFFICIENT_DATA,
            )

        fields = [
            self._compare_field(
                ComparisonField.CATEGORY,
                gemini_analysis.category.value,
                ollama_analysis.category.value,
            ),
            self._compare_field(
                ComparisonField.URGENCY,
                gemini_analysis.urgency.value,
                ollama_analysis.urgency.value,
            ),
            self._compare_field(
                ComparisonField.ACTION,
                gemini_analysis.recommendation.action.value,
                ollama_analysis.recommendation.action.value,
            ),
            self._compare_field(
                ComparisonField.TARGET_LAP,
                gemini_analysis.recommendation.target_lap,
                ollama_analysis.recommendation.target_lap,
            ),
            self._compare_field(
                ComparisonField.TYRE_COMPOUND,
                self._enum_value(
                    gemini_analysis.recommendation.tyre_compound
                ),
                self._enum_value(
                    ollama_analysis.recommendation.tyre_compound
                ),
            ),
            self._compare_confidence(
                gemini_analysis.confidence,
                ollama_analysis.confidence,
            ),
        ]

        return Comparison(
            status=ComparisonStatus.COMPLETED,
            fields=fields,
            strategic_agreement=self._strategic_agreement(
                gemini_analysis,
                ollama_analysis,
            ),
            confidence_difference=abs(
                gemini_analysis.confidence
                - ollama_analysis.confidence
            ),
            target_lap_difference=self._target_lap_difference(
                gemini_analysis,
                ollama_analysis,
            ),
        )

    # ======================================================================
    # VALIDATION
    # ======================================================================

    @staticmethod
    def _analyses_are_comparable(
        gemini_analysis: AIAnalysis,
        ollama_analysis: AIAnalysis,
    ) -> bool:
        """Comprueba que ambos análisis pueden compararse."""

        return (
            gemini_analysis.provider.value == "gemini"
            and ollama_analysis.provider.value == "ollama"
            and gemini_analysis.status == AnalysisStatus.SUCCESS
            and ollama_analysis.status == AnalysisStatus.SUCCESS
        )

    # ======================================================================
    # FIELD COMPARISON
    # ======================================================================

    @staticmethod
    def _compare_field(
        field: ComparisonField,
        gemini_value,
        ollama_value,
    ) -> FieldComparison:
        """Compara dos valores discretos."""

        if gemini_value is None and ollama_value is None:
            agreement = AgreementLevel.AGREE

        elif gemini_value is None or ollama_value is None:
            agreement = AgreementLevel.NOT_COMPARABLE

        elif gemini_value == ollama_value:
            agreement = AgreementLevel.AGREE

        else:
            agreement = AgreementLevel.DISAGREE

        return FieldComparison(
            field=field,
            gemini_value=gemini_value,
            ollama_value=ollama_value,
            agreement=agreement,
        )

    @staticmethod
    def _compare_confidence(
        gemini_confidence: float,
        ollama_confidence: float,
    ) -> FieldComparison:
        """Compara las confianzas de ambos modelos."""

        difference = abs(
            gemini_confidence - ollama_confidence
        )

        if difference == 0:
            agreement = AgreementLevel.AGREE
        elif difference <= 0.20:
            agreement = AgreementLevel.CLOSE
        else:
            agreement = AgreementLevel.DISAGREE

        return FieldComparison(
            field=ComparisonField.CONFIDENCE,
            gemini_value=gemini_confidence,
            ollama_value=ollama_confidence,
            agreement=agreement,
        )

    # ======================================================================
    # STRATEGIC AGREEMENT
    # ======================================================================

    @staticmethod
    def _strategic_agreement(
        gemini_analysis: AIAnalysis,
        ollama_analysis: AIAnalysis,
    ) -> AgreementLevel:
        """
        Determina el acuerdo estratégico.

        La acción es el elemento estratégico principal.
        Una diferencia en target_lap no implica necesariamente
        desacuerdo estratégico.
        """

        gemini_action = gemini_analysis.recommendation.action
        ollama_action = ollama_analysis.recommendation.action

        if gemini_action == ollama_action:
            return AgreementLevel.AGREE

        return AgreementLevel.DISAGREE

    # ======================================================================
    # HELPERS
    # ======================================================================

    @staticmethod
    def _target_lap_difference(
        gemini_analysis: AIAnalysis,
        ollama_analysis: AIAnalysis,
    ) -> int | None:
        """Calcula la diferencia absoluta entre vueltas objetivo."""

        gemini_lap = gemini_analysis.recommendation.target_lap
        ollama_lap = ollama_analysis.recommendation.target_lap

        if gemini_lap is None or ollama_lap is None:
            return None

        return abs(gemini_lap - ollama_lap)

    @staticmethod
    def _enum_value(value):
        """Obtiene el valor de un enum o devuelve None."""

        if value is None:
            return None

        return value.value