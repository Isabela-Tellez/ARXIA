"""
Orquestador principal de ARXIA.

Coordina los proveedores de IA, la comparación de modelos,
la evaluación de riesgo y la decisión final.

No contiene lógica propia de comparación, riesgo o decisión.
Delega cada responsabilidad al componente correspondiente.
"""

from core.application.comparison_engine import ComparisonEngine
from core.application.decision_engine import DecisionEngine
from core.application.risk_engine import RiskEngine
from core.domain.enums import DecisionType, ReviewStatus
from core.domain.schemas import (
    AIAnalysis,
    ArxiaResult,
    HumanReview,
    RaceEvent,
)


class ArxiaCore:
    """Orquesta el pipeline completo de decisión de ARXIA."""

    def __init__(
        self,
        gemini_provider,
        ollama_provider,
        comparison_engine: ComparisonEngine,
        risk_engine: RiskEngine,
        decision_engine: DecisionEngine,
    ):
        """
        Inicializa ARXIA con sus proveedores y motores de aplicación.

        Los proveedores se reciben mediante inyección de dependencias
        para permitir utilizar implementaciones reales o mocks.
        """

        self.gemini_provider = gemini_provider
        self.ollama_provider = ollama_provider
        self.comparison_engine = comparison_engine
        self.risk_engine = risk_engine
        self.decision_engine = decision_engine

    def process(
        self,
        race_event: RaceEvent,
    ) -> ArxiaResult:
        """
        Ejecuta el pipeline completo de ARXIA.

        Flujo:

        1. Analiza el evento con Gemini.
        2. Analiza el evento con Ollama.
        3. Compara ambos análisis.
        4. Evalúa el riesgo de automatización.
        5. Genera la decisión final.
        6. Crea una revisión humana si es necesaria.
        7. Construye y devuelve el resultado completo.
        """

        # ------------------------------------------------------------------
        # Paso 1: Análisis de Gemini
        # ------------------------------------------------------------------

        gemini_analysis = self.gemini_provider.analyze(
            race_event,
        )

        # ------------------------------------------------------------------
        # Paso 2: Análisis de Ollama
        # ------------------------------------------------------------------

        ollama_analysis = self.ollama_provider.analyze(
            race_event,
        )

        # ------------------------------------------------------------------
        # Paso 3: Comparación de modelos
        # ------------------------------------------------------------------

        comparison = self.comparison_engine.compare(
            gemini_analysis=gemini_analysis,
            ollama_analysis=ollama_analysis,
        )

        # ------------------------------------------------------------------
        # Paso 4: Evaluación de riesgo
        # ------------------------------------------------------------------

        risk_assessment = self.risk_engine.assess(
            race_event=race_event,
            gemini_analysis=gemini_analysis,
            ollama_analysis=ollama_analysis,
            comparison=comparison,
        )

        # ------------------------------------------------------------------
        # Paso 5: Decisión final
        # ------------------------------------------------------------------

        decision = self.decision_engine.decide(
            gemini_analysis=gemini_analysis,
            ollama_analysis=ollama_analysis,
            comparison=comparison,
            risk_assessment=risk_assessment,
        )

        # ------------------------------------------------------------------
        # Paso 6: Revisión humana
        # ------------------------------------------------------------------

        human_review = self._build_human_review(
            decision=decision,
        )

        # ------------------------------------------------------------------
        # Paso 7: Resultado completo
        # ------------------------------------------------------------------

        return ArxiaResult(
            race_event=race_event,
            gemini_analysis=gemini_analysis,
            ollama_analysis=ollama_analysis,
            comparison=comparison,
            risk_assessment=risk_assessment,
            decision=decision,
            human_review=human_review,
        )

    @staticmethod
    def _build_human_review(
        decision,
    ) -> HumanReview | None:
        """
        Crea una revisión humana cuando la decisión lo requiere.

        Una decisión automática no genera ningún objeto de revisión.
        Una decisión de revisión humana comienza siempre en estado
        PENDING y sin decisión final del ingeniero.
        """

        if decision.decision == DecisionType.AUTOMATIC:
            return None

        return HumanReview(
            status=ReviewStatus.PENDING,
        )