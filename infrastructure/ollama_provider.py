"""
Proveedor real basado en Ollama para ARXIA.
"""

import json
import os
import time

import requests
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


class OllamaRecommendation(BaseModel):
    """Respuesta estratégica generada por Ollama."""

    action: RecommendationAction
    target_lap: int | None = None
    tyre_compound: TyreCompound | None = None
    confidence: float
    rationale: str
    alternative_action: RecommendationAction | None = None


class OllamaAnalysisResponse(BaseModel):
    """Payload estructurado esperado de Ollama."""

    category: AnalysisCategory
    urgency: AnalysisUrgency
    confidence: float
    summary: str
    reasoning: str
    recommendation: OllamaRecommendation


class OllamaProvider:
    """Proveedor de IA local basado en Ollama."""

    DEFAULT_MODEL = "llama3.2:3b"
    DEFAULT_BASE_URL = "http://localhost:11434"
    DEFAULT_TIMEOUT = 120.0
    DEFAULT_NUM_PREDICT = 256

    def __init__(
        self,
        model: str | None = None,
        base_url: str | None = None,
        timeout: float = DEFAULT_TIMEOUT,
        num_predict: int = DEFAULT_NUM_PREDICT,
    ):
        """Inicializa el proveedor Ollama."""

        self.model = (
            model
            or os.getenv("OLLAMA_MODEL")
            or self.DEFAULT_MODEL
        ).strip()

        self.base_url = (
            base_url
            or os.getenv("OLLAMA_BASE_URL")
            or self.DEFAULT_BASE_URL
        ).strip().rstrip("/")

        if not self.model:
            raise ValueError(
                "Ollama model cannot be empty"
            )

        if not self.base_url:
            raise ValueError(
                "Ollama base URL cannot be empty"
            )

        if timeout <= 0:
            raise ValueError(
                "Ollama timeout must be greater than zero"
            )

        if num_predict <= 0:
            raise ValueError(
                "Ollama num_predict must be greater than zero"
            )

        self.timeout = timeout
        self.num_predict = num_predict

    def analyze(
        self,
        race_event: RaceEvent,
    ) -> AIAnalysis:
        """Analiza un evento de carrera utilizando Ollama."""

        started_at = time.perf_counter()

        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": self._build_prompt(race_event),
                    "stream": False,
                    "format": "json",
                    "options": {
                        "temperature": 0,
                        "num_predict": self.num_predict,
                    },
                },
                timeout=self.timeout,
            )

            response.raise_for_status()

            parsed = self._parse_response(response)

            return AIAnalysis(
                provider=Provider.OLLAMA,
                model=self.model,
                status=AnalysisStatus.SUCCESS,
                category=parsed.category,
                urgency=parsed.urgency,
                confidence=parsed.confidence,
                summary=parsed.summary,
                reasoning=parsed.reasoning,
                recommendation=Recommendation.model_validate(
                    parsed.recommendation.model_dump()
                ),
                metrics=self._build_metrics(
                    response,
                    (time.perf_counter() - started_at) * 1000,
                ),
                error=None,
            )

        except requests.Timeout:
            return self._build_error_analysis(
                AnalysisStatus.TIMEOUT,
                "Ollama request timed out.",
                (time.perf_counter() - started_at) * 1000,
            )

        except (
            ValidationError,
            ValueError,
            KeyError,
            TypeError,
        ) as exc:
            return self._build_error_analysis(
                AnalysisStatus.INVALID,
                f"Invalid Ollama response: {exc}",
                (time.perf_counter() - started_at) * 1000,
            )

        except requests.RequestException as exc:
            return self._build_error_analysis(
                AnalysisStatus.ERROR,
                f"Ollama request failed: {exc}",
                (time.perf_counter() - started_at) * 1000,
            )

        except Exception as exc:
            return self._build_error_analysis(
                AnalysisStatus.ERROR,
                f"Ollama request failed: {exc}",
                (time.perf_counter() - started_at) * 1000,
            )

    @staticmethod
    def _build_prompt(
        race_event: RaceEvent,
    ) -> str:
        """Construye el prompt enviado a Ollama."""

        weather = race_event.weather

        weather_context = (
            "unknown"
            if weather is None
            else (
                f"condition={weather.condition.value}, "
                f"temperature_c={weather.temperature_c}, "
                f"track_temperature_c={weather.track_temperature_c}, "
                f"rain_probability={weather.rain_probability}, "
                f"wind_speed_kmh={weather.wind_speed_kmh}"
            )
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
Race context: {race_event.race_context or "none"}
Description: {race_event.description}

Instructions:

Analyze only the information provided.

Do not invent telemetry, lap times, tyre degradation values,
weather measurements, or race events.

IMPORTANT:
event_type and category are different fields.

event_type describes the type of event that occurred.
category describes the category of your analysis.

NEVER copy the event_type value into category.

Allowed category values are ONLY:
"tyre_strategy"
"race_strategy"
"weather"
"mechanical"
"safety"
"position"
"other"

Allowed urgency values are ONLY:
"low"
"medium"
"high"
"critical"

Allowed recommendation action values are ONLY:
"pit_stop"
"stay_out"
"push"
"manage_tyres"
"defend"
"attack"
"no_action"

Allowed tyre compound values are ONLY:
"soft"
"medium"
"hard"
"intermediate"
"wet"

Return ONLY valid JSON using exactly this structure:

{{
"category": "...",
"urgency": "...",
"confidence": 0.0,
"summary": "...",
"reasoning": "...",
"recommendation": {{
"action": "...",
"target_lap": null,
"tyre_compound": null,
"confidence": 0.0,
"rationale": "...",
"alternative_action": null
}}
}}

Confidence values must be numbers between 0 and 1.

Set target_lap to null when it cannot be reasonably determined.

Set tyre_compound to null when a tyre change is not applicable.

Set alternative_action to null when there is no reasonable alternative.
""".strip()

    @staticmethod
    def _parse_response(
        response,
    ) -> OllamaAnalysisResponse:
        """Convierte la respuesta HTTP de Ollama en un DTO."""

        try:
            data = response.json()
        except ValueError as exc:
            raise ValueError(
                "Ollama returned invalid HTTP JSON"
            ) from exc

        raw_response = data.get("response", "")

        if not isinstance(raw_response, str):
            raise ValueError(
                "Ollama response field must be a string"
            )

        if not raw_response.strip():
            raise ValueError(
                "Ollama returned an empty response"
            )

        try:
            parsed_json = json.loads(raw_response)
        except json.JSONDecodeError as exc:
            raise ValueError(
                f"Ollama returned invalid JSON: {exc}"
            ) from exc

        return OllamaAnalysisResponse.model_validate(
            parsed_json
        )

    @staticmethod
    def _build_metrics(
        response,
        latency_ms: float,
    ) -> ModelMetrics:
        """Construye las métricas de Ollama."""

        try:
            data = response.json()
        except ValueError:
            data = {}

        input_tokens = int(
            data.get("prompt_eval_count", 0) or 0
        )

        output_tokens = int(
            data.get("eval_count", 0) or 0
        )

        return ModelMetrics(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=input_tokens + output_tokens,
            latency_ms=latency_ms,
            cost=0.0,
            retries=0,
        )

    def _build_error_analysis(
        self,
        status: AnalysisStatus,
        error: str,
        latency_ms: float,
    ) -> AIAnalysis:
        """Construye un AIAnalysis para una ejecución fallida."""

        return AIAnalysis(
            provider=Provider.OLLAMA,
            model=self.model,
            status=status,
            category=AnalysisCategory.OTHER,
            urgency=AnalysisUrgency.CRITICAL,
            confidence=0.0,
            summary="Ollama analysis failed.",
            reasoning="No valid analysis was produced.",
            recommendation=Recommendation(
                action=RecommendationAction.NO_ACTION,
                target_lap=None,
                tyre_compound=None,
                confidence=0.0,
                rationale="No recommendation available.",
                alternative_action=None,
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