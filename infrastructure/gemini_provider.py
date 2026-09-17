"""
Proveedor real de Gemini para ARXIA.

Se encarga exclusivamente de:
- comunicarse con Gemini,
- construir el prompt,
- validar la respuesta,
- transformar la respuesta en un AIAnalysis válido.

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
# GEMINI RESPONSE SCHEMAS
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
    """Respuesta estructurada esperada de Gemini."""

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

    # Número máximo de reintentos para errores recuperables.
    DEFAULT_MAX_RETRIES = 2

    # Tiempo base entre reintentos.
    DEFAULT_RETRY_DELAY = 30.0

    def __init__(
        self,
        api_key: str | None = None,
        model: str = DEFAULT_MODEL,
        max_retries: int = DEFAULT_MAX_RETRIES,
        retry_delay: float = DEFAULT_RETRY_DELAY,
    ):
        """
        Inicializa el proveedor Gemini.

        Args:
            api_key:
                API key de Gemini. Si no se proporciona, se obtiene
                de GEMINI_API_KEY.

            model:
                Modelo de Gemini utilizado.

            max_retries:
                Número máximo de reintentos ante errores recuperables.

            retry_delay:
                Tiempo base de espera entre reintentos.
        """

        self.api_key = api_key or os.getenv("GEMINI_API_KEY")

        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is required")

        if not model.strip():
            raise ValueError("Gemini model cannot be empty")

        if max_retries < 0:
            raise ValueError(
                "Gemini max retries cannot be negative"
            )

        if retry_delay < 0:
            raise ValueError(
                "Gemini retry delay cannot be negative"
            )

        self.model = model.strip()
        self.max_retries = max_retries
        self.retry_delay = retry_delay

        self.client = genai.Client(
            api_key=self.api_key,
        )

    # =========================================================================
    # PUBLIC API
    # =========================================================================

    def analyze(
        self,
        race_event: RaceEvent,
    ) -> AIAnalysis:
        """
        Analiza un evento de carrera utilizando Gemini.

        Si Gemini devuelve un error temporal recuperable, se realizan
        reintentos antes de considerar la ejecución como fallida.
        """

        started_at = time.perf_counter()
        retries = 0

        try:
            response = self._generate_with_retry(
                race_event=race_event,
                retries_holder=[0],
            )

            retries = self._last_retry_count

            latency_ms = self._latency_ms(started_at)

            parsed_response = self._parse_response(response)

            metrics = self._build_metrics(
                response=response,
                latency_ms=latency_ms,
                retries=retries,
            )

            return self._build_success_analysis(
                parsed_response=parsed_response,
                metrics=metrics,
            )

        except TimeoutError:
            latency_ms = self._latency_ms(started_at)

            return self._build_error_analysis(
                status=AnalysisStatus.TIMEOUT,
                error="Gemini request timed out.",
                latency_ms=latency_ms,
                retries=retries,
            )

        except (ValidationError, ValueError) as exc:
            latency_ms = self._latency_ms(started_at)

            return self._build_error_analysis(
                status=AnalysisStatus.INVALID,
                error=f"Invalid Gemini response: {exc}",
                latency_ms=latency_ms,
                retries=retries,
            )

        except Exception as exc:
            latency_ms = self._latency_ms(started_at)

            error_message = self._format_gemini_error(exc)

            return self._build_error_analysis(
                status=AnalysisStatus.ERROR,
                error=error_message,
                latency_ms=latency_ms,
                retries=retries,
            )

    # =========================================================================
    # GEMINI REQUEST
    # =========================================================================

    def _generate_with_retry(
        self,
        *,
        race_event: RaceEvent,
        retries_holder: list[int],
    ):
        """
        Ejecuta la petición a Gemini aplicando reintentos.

        Solo se reintentan errores que parecen ser temporales,
        especialmente respuestas 429 / RESOURCE_EXHAUSTED.
        """

        self._last_retry_count = 0

        for attempt in range(self.max_retries + 1):
            try:
                response = self.client.models.generate_content(
                    model=self.model,
                    contents=self._build_prompt(race_event),
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        response_schema=GeminiAnalysisResponse,
                    ),
                )

                return response

            except Exception as exc:
                if not self._is_retryable_error(exc):
                    raise

                if attempt >= self.max_retries:
                    raise

                self._last_retry_count += 1
                retries_holder[0] = self._last_retry_count

                delay = self._get_retry_delay(
                    exc=exc,
                    attempt=attempt,
                )

                time.sleep(delay)

        raise RuntimeError(
            "Gemini request failed after all retries."
        )

    # =========================================================================
    # RETRY HELPERS
    # =========================================================================

    @staticmethod
    def _is_retryable_error(
        exc: Exception,
    ) -> bool:
        """
        Determina si un error de Gemini puede ser reintentado.

        Principalmente se contemplan:
        - HTTP 429
        - RESOURCE_EXHAUSTED
        - rate limit
        - quota temporal
        """

        message = str(exc).lower()

        retryable_markers = (
            "429",
            "resource_exhausted",
            "resource exhausted",
            "rate limit",
            "rate_limit",
            "too many requests",
        )

        return any(
            marker in message
            for marker in retryable_markers
        )

    def _get_retry_delay(
        self,
        *,
        exc: Exception,
        attempt: int,
    ) -> float:
        """
        Obtiene el tiempo de espera antes del siguiente intento.

        Si Gemini proporciona un retry delay explícito, se intenta
        utilizarlo. Si no, se utiliza un backoff sencillo.
        """

        retry_delay = self._extract_retry_delay(exc)

        if retry_delay is not None:
            return retry_delay

        # Backoff:
        # intento 0 -> retry_delay
        # intento 1 -> retry_delay * 2
        return self.retry_delay * (2**attempt)

    @staticmethod
    def _extract_retry_delay(
        exc: Exception,
    ) -> float | None:
        """
        Intenta extraer el tiempo de espera indicado por Gemini.

        Gemini suele devolver mensajes similares a:
        'Please retry in 25.5s'
        o
        'retryDelay: 25s'
        """

        message = str(exc).lower()

        markers = (
            "retry in ",
            "retrydelay:",
            "retry_delay:",
        )

        for marker in markers:
            if marker not in message:
                continue

            remaining = message.split(
                marker,
                1,
            )[1].strip()

            number = ""

            for character in remaining:
                if character.isdigit() or character == ".":
                    number += character
                else:
                    break

            if number:
                try:
                    return float(number)
                except ValueError:
                    pass

        return None

    @staticmethod
    def _format_gemini_error(
        exc: Exception,
    ) -> str:
        """
        Convierte errores técnicos de Gemini en mensajes más útiles.
        """

        message = str(exc)

        lowered = message.lower()

        if (
            "429" in lowered
            or "resource_exhausted" in lowered
            or "resource exhausted" in lowered
        ):
            return (
                "Gemini quota exceeded. "
                "The configured Gemini API project has reached "
                "its current request limit."
            )

        if "timeout" in lowered:
            return "Gemini request timed out."

        return f"Gemini request failed: {exc}"

    # =========================================================================
    # PROMPT
    # =========================================================================

    @staticmethod
    def _build_prompt(
        race_event: RaceEvent,
    ) -> str:
        """Construye el prompt enviado a Gemini."""

        weather = race_event.weather

        if weather is None:
            weather_context = "unknown"
        else:
            weather_context = (
                f"condition={weather.condition.value}, "
                f"temperature_c={weather.temperature_c}, "
                f"track_temperature_c={weather.track_temperature_c}, "
                f"rain_probability={weather.rain_probability}, "
                f"wind_speed_kmh={weather.wind_speed_kmh}"
            )

        if race_event.tyre_compound is None:
            tyre_compound = "unknown"
        else:
            tyre_compound = race_event.tyre_compound.value

        if race_event.track_condition is None:
            track_condition = "unknown"
        else:
            track_condition = race_event.track_condition.value

        race_context = (
            race_event.race_context
            if race_event.race_context
            else "none"
        )

        return f"""
You are ARXIA, an AI motorsport race strategy analyst.

Analyze the following race event and provide a structured
strategic assessment.

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
Race context: {race_context}
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

    # =========================================================================
    # RESPONSE PARSING
    # =========================================================================

    @staticmethod
    def _parse_response(
        response,
    ) -> GeminiAnalysisResponse:
        """
        Convierte la respuesta de Gemini en nuestro DTO estructurado.

        Preferimos response.parsed cuando el SDK lo proporciona.
        Como fallback utilizamos response.text.
        """

        parsed = getattr(
            response,
            "parsed",
            None,
        )

        if isinstance(
            parsed,
            GeminiAnalysisResponse,
        ):
            return parsed

        if parsed is not None:
            return GeminiAnalysisResponse.model_validate(
                parsed
            )

        text = getattr(
            response,
            "text",
            None,
        )

        if not text:
            raise ValueError(
                "Gemini returned an empty response"
            )

        return GeminiAnalysisResponse.model_validate_json(
            text
        )

    # =========================================================================
    # SUCCESS ANALYSIS
    # =========================================================================

    def _build_success_analysis(
        self,
        *,
        parsed_response: GeminiAnalysisResponse,
        metrics: ModelMetrics,
    ) -> AIAnalysis:
        """Construye un AIAnalysis exitoso."""

        recommendation = parsed_response.recommendation

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
                action=recommendation.action,
                target_lap=recommendation.target_lap,
                tyre_compound=recommendation.tyre_compound,
                confidence=recommendation.confidence,
                rationale=recommendation.rationale,
                alternative_action=(
                    recommendation.alternative_action
                ),
            ),
            metrics=metrics,
            error=None,
        )

    # =========================================================================
    # METRICS
    # =========================================================================

    @staticmethod
    def _build_metrics(
        *,
        response,
        latency_ms: float,
        retries: int = 0,
    ) -> ModelMetrics:
        """Construye las métricas de la ejecución de Gemini."""

        usage = getattr(
            response,
            "usage_metadata",
            None,
        )

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
            retries=retries,
        )

    # =========================================================================
    # ERROR ANALYSIS
    # =========================================================================

    def _build_error_analysis(
        self,
        *,
        status: AnalysisStatus,
        error: str,
        latency_ms: float,
        retries: int = 0,
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
                retries=retries,
            ),
            error=error,
        )

    # =========================================================================
    # HELPERS
    # =========================================================================

    @staticmethod
    def _latency_ms(
        started_at: float,
    ) -> float:
        """Calcula la latencia en milisegundos."""

        return (
            time.perf_counter() - started_at
        ) * 1000