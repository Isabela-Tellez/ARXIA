"""
Proveedor real de Gemini para ARXIA.
Se encarga exclusivamente de comunicarse con Gemini y transformar
su respuesta estructurada en un AIAnalysis válido del dominio.
No contiene lógica de comparación, evaluación de riesgo ni decisión.
"""

import os
import time

from google import genai
from google.genai import types
from pydantic import BaseModel, ValidationError

from core.domain.enums import (
    AnalysisCategory,
    AnalysisStatus,
    AnalysisUrgency,
    Provider,
    RecommendationAction,
    TyreCompound,
)
from core.domain.schemas import (
    AIAnalysis,
    ModelMetrics,
    RaceEvent,
    Recommendation,
)


# ============================================================================
# GEMINI RESPONSE SCHEMA
# ============================================================================

class GeminiRecommendation(BaseModel):
    """Respuesta estratégica generada por Gemini."""
    action: RecommendationAction
    target_lap: int | None = None
    tyre_compound: TyreCompound | None = None
    confidence: float
    rationale: str
    alternative_action: RecommendationAction | None = None


class GeminiAnalysisResponse(BaseModel):
    """Payload estructurado que esperamos recibir de Gemini."""
    category: AnalysisCategory
    urgency: AnalysisUrgency
    confidence: float
    summary: str
    reasoning: str
    recommendation: GeminiRecommendation


# ============================================================================
# PROVIDER
# ============================================================================

class GeminiProvider:
    """Proveedor de IA basado en Google Gemini."""
    DEFAULT_MODEL = "gemini-3.6-flash"

    def __init__(
        self,
        api_key: str | None = None,
        model: str = DEFAULT_MODEL,
    ):
        """
        Inicializa el proveedor Gemini.

        Args:
            api_key:
                API key de Gemini. Si no se proporciona, se obtiene
                de la variable de entorno GEMINI_API_KEY.

            model:
                Modelo de Gemini utilizado para el análisis.
        """
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")

        if not self.api_key:
            raise ValueError(
                "GEMINI_API_KEY is required"
            )

        if not model.strip():
            raise ValueError(
                "Gemini model cannot be empty"
            )

        self.model = model.strip()

        self.client = genai.Client(
            api_key=self.api_key,
        )

    # ========================================================================
    # PUBLIC API
    # ========================================================================

    def analyze(
        self,
        race_event: RaceEvent,
    ) -> AIAnalysis:
        """
        Analiza un evento de carrera utilizando Gemini.

        Gemini produce únicamente el análisis estratégico.
        El provider se encarga de construir el AIAnalysis completo.
        """
        started_at = time.perf_counter()

        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=self._build_prompt(race_event),
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=GeminiAnalysisResponse,
                ),
            )

            latency_ms = self._latency_ms(started_at)

            parsed_response = self._parse_response(response)

            metrics = self._build_metrics(
                response=response,
                latency_ms=latency_ms,
            )

            return AIAnalysis(
                provider=Provider.GEMINI,
                model=self.model,
                status=AnalysisStatus.SUCCESS,
                category=parsed_response.category,
                urgency=parsed_response.urgency,
                confidence=parsed_response.confidence,
                summary=parsed_response.summary,
                reasoning=parsed_response.reasoning,
                recommendation=Recommendation(
                    action=parsed_response.recommendation.action,
                    target_lap=parsed_response.recommendation.target_lap,
                    tyre_compound=(
                        parsed_response.recommendation.tyre_compound
                    ),
                    confidence=(
                        parsed_response.recommendation.confidence
                    ),
                    rationale=(
                        parsed_response.recommendation.rationale
                    ),
                    alternative_action=(
                        parsed_response.recommendation.alternative_action
                    ),
                ),
                metrics=metrics,
                error=None,
            )

        except TimeoutError:
            latency_ms = self._latency_ms(started_at)

            return self._build_error_analysis(
                status=AnalysisStatus.TIMEOUT,
                error="Gemini request timed out.",
                latency_ms=latency_ms,
            )

        except (ValidationError, ValueError) as exc:
            latency_ms = self._latency_ms(started_at)

            return self._build_error_analysis(
                status=AnalysisStatus.INVALID,
                error=f"Invalid Gemini response: {exc}",
                latency_ms=latency_ms,
            )

        except Exception as exc:
            latency_ms = self._latency_ms(started_at)

            return self._build_error_analysis(
                status=AnalysisStatus.ERROR,
                error=f"Gemini request failed: {exc}",
                latency_ms=latency_ms,
            )

    # ========================================================================
    # PROMPT
    # ========================================================================

    @staticmethod
    def _build_prompt(
        race_event: RaceEvent,
    ) -> str:
        """Construye el prompt enviado a Gemini."""
        weather = race_event.weather

        weather_context = "unknown"

        if weather is not None:
            weather_context = (
                f"condition={weather.condition.value}, "
                f"temperature_c={weather.temperature_c}, "
                f"track_temperature_c={weather.track_temperature_c}, "
                f"rain_probability={weather.rain_probability}, "
                f"wind_speed_kmh={weather.wind_speed_kmh}"
            )

        tyre_compound = (
            race_event.tyre_compound.value
            if race_event.tyre_compound is not None
            else "unknown"
        )

        track_condition = (
            race_event.track_condition.value
            if race_event.track_condition is not None
            else "unknown"
        )

        return f"""
You are ARXIA, an AI motorsport race strategy analyst.
Analyze the following race event and provide a structured strategic
assessment.
Race event:

Circuit: {race_event.circuit}
Session: {race_event.session.value}
Lap: {race_event.lap}
Driver: {race_event.driver}
Team: {race_event.team}
Position: {race_event.position}
Event type: {race_event.event_type.value}
Current tyre compound: {tyre_compound}
Track condition: {track_condition}
Weather: {weather_context}
Race context: {race_event.race_context or "none"}
Description: {race_event.description}
Instructions:

Analyze only the information provided.
Do not invent telemetry, lap times, tyre degradation values,
weather measurements, or race events.
Identify the most appropriate strategic response.
Give a confidence value between 0 and 1.
Give recommendation confidence between 0 and 1.
Use only the allowed enum values for category, urgency, action,
tyre compound, and alternative action.
Set target_lap to null when a target lap cannot be reasonably
determined.
Set tyre_compound to null when a tyre change is not applicable.
Keep the summary concise.
Explain the reasoning behind the recommendation.
""".strip()

    # ========================================================================
    # RESPONSE PARSING
    # ========================================================================

    @staticmethod
    def _parse_response(
        response,
    ) -> GeminiAnalysisResponse:
        """
        Convierte la respuesta de Gemini en nuestro DTO estructurado.
        Preferimos response.parsed cuando el SDK lo proporciona.
        Como fallback utilizamos response.text.
        """
        parsed = getattr(response, "parsed", None)

        if isinstance(parsed, GeminiAnalysisResponse):
            return parsed

        if parsed is not None:
            return GeminiAnalysisResponse.model_validate(parsed)

        text = getattr(response, "text", None)

        if not text:
            raise ValueError(
                "Gemini returned an empty response"
            )

        return GeminiAnalysisResponse.model_validate_json(text)

    # ========================================================================
    # METRICS
    # ========================================================================

    @staticmethod
    def _build_metrics(
        *,
        response,
        latency_ms: float,
    ) -> ModelMetrics:
        """Construye las métricas de la ejecución de Gemini."""
        usage = getattr(response, "usage_metadata", None)

        input_tokens = int(
            getattr(
                usage,
                "prompt_token_count",
                0,
            )
            or 0
        )

        output_tokens = int(
            getattr(
                usage,
                "candidates_token_count",
                0,
            )
            or 0
        )

        total_tokens = input_tokens + output_tokens

        return ModelMetrics(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total_tokens,
            latency_ms=latency_ms,
            cost=0.0,
            retries=0,
        )

    # ========================================================================
    # ERRORS
    # ========================================================================

    def _build_error_analysis(
        self,
        *,
        status: AnalysisStatus,
        error: str,
        latency_ms: float,
    ) -> AIAnalysis:
        """Construye un AIAnalysis para una ejecución fallida."""
        return AIAnalysis(
            provider=Provider.GEMINI,
            model=self.model,
            status=status,
            category=AnalysisCategory.OTHER,
            urgency=AnalysisUrgency.MEDIUM,
            confidence=0.0,
            summary="Gemini analysis failed.",
            reasoning="No valid analysis was produced.",
            recommendation=Recommendation(
                action=RecommendationAction.NO_ACTION,
                target_lap=None,
                tyre_compound=None,
                confidence=0.0,
                rationale="No recommendation available.",
            ),
            metrics=ModelMetrics(
                input_tokens=0,
                output_tokens=0,
                total_tokens=0,
                latency_ms=latency_ms,
                cost=0.0,
                retries=0,
            ),
            error=error,
        )

    # ========================================================================
    # HELPERS
    # ========================================================================

    @staticmethod
    def _latency_ms(
        started_at: float,
    ) -> float:
        """Calcula la latencia en milisegundos."""
        return (
            time.perf_counter() - started_at
        ) * 1000