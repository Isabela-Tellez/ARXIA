"""
Proveedor de modelos basado en Ollama.
Permite a ARXIA utilizar un modelo local mediante Ollama sin
acoplar el dominio ni los motores de decisión a la implementación
concreta del proveedor.
"""

import json
import time
import requests

from domain.enums import (
    AnalysisCategory,
    AnalysisStatus,
    AnalysisUrgency,
    Provider,
    RecommendationAction,
)
from domain.schemas import (
    AIAnalysis,
    ModelMetrics,
    RaceEvent,
    Recommendation,
)


class OllamaProvider:
    """Proveedor de modelos locales mediante la API de Ollama."""

    def __init__(
        self,
        model: str = "llama3.2:3b",
        base_url: str = "http://localhost:11434",
        timeout: float = 60.0,
    ):
        """
        Inicializa el proveedor de Ollama.

        Args:
            model:
                Nombre del modelo local utilizado por Ollama.

            base_url:
                URL base de la API HTTP de Ollama.

            timeout:
                Tiempo máximo de espera de la petición HTTP,
                expresado en segundos.
        """
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    # ======================================================================
    # PUBLIC API
    # ======================================================================

    def analyze(self, race_event: RaceEvent) -> AIAnalysis:
        """
        Analiza un evento de carrera utilizando Ollama.

        El flujo es:

            RaceEvent
                ↓
            Prompt
                ↓
            Ollama API
                ↓
            JSON
                ↓
            AIAnalysis

        Si Ollama devuelve un error, una respuesta vacía o una
        respuesta JSON inválida, se devuelve igualmente un
        AIAnalysis con status ERROR.
        """
        start_time = time.perf_counter()

        # Construimos el prompt a partir del mismo RaceEvent
        # recibido por cualquier otro provider.
        prompt = self._build_prompt(race_event)

        try:
            # Realizamos la petición a la API de Ollama.
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "format": "json",
                },
                timeout=self.timeout,
            )

            # Si Ollama devuelve un código HTTP de error,
            # requests lanzará una excepción.
            response.raise_for_status()

            # Convertimos la respuesta HTTP a un diccionario.
            data = response.json()

            # Ollama devuelve el contenido generado dentro
            # de la propiedad "response".
            raw_response = data.get("response", "")

            # Una respuesta vacía no puede convertirse en análisis.
            if not raw_response.strip():
                return self._build_error_analysis(
                    error="Ollama returned an empty response",
                    start_time=start_time,
                )

            # El modelo debe devolver exclusivamente JSON.
            parsed_result = json.loads(raw_response)

            # Convertimos el JSON recibido en el objeto de dominio
            # AIAnalysis.
            return self._build_analysis(
                parsed_result=parsed_result,
                data=data,
                start_time=start_time,
            )

        except requests.RequestException as exc:
            # Error de conexión, timeout o error HTTP.
            return self._build_error_analysis(
                error=str(exc),
                start_time=start_time,
            )

        except (ValueError, KeyError, TypeError) as exc:
            # Error al interpretar la respuesta del modelo.
            return self._build_error_analysis(
                error=f"Invalid Ollama response: {exc}",
                start_time=start_time,
            )

    # ======================================================================
    # PROMPT
    # ======================================================================

    def _build_prompt(
        self,
        race_event: RaceEvent,
    ) -> str:
        """
        Construye el prompt estructurado enviado a Ollama.

        El objetivo es pedir al modelo exactamente la estructura
        que ARXIA necesita para construir AIAnalysis.
        """
        weather = race_event.weather
        weather_context = "unknown"

        if weather is not None:
            weather_context = weather.condition.value

        return f"""
Analyze the following motorsport race event.
Circuit: {race_event.circuit}
Session: {race_event.session.value}
Lap: {race_event.lap}
Driver: {race_event.driver}
Team: {race_event.team}
Position: {race_event.position}
Event type: {race_event.event_type.value}
Current tyre compound: {
    race_event.tyre_compound.value
    if race_event.tyre_compound
    else "unknown"
}
Track condition: {
    race_event.track_condition.value
    if race_event.track_condition
    else "unknown"
}
Weather: {weather_context}
Race context:
{race_event.race_context or "unknown"}
Event description:
{race_event.description}

Return ONLY valid JSON with exactly this structure:
{{
  "category": "race_strategy",
  "urgency": "medium",
  "confidence": 0.90,
  "summary": "Brief summary of the analysis.",
  "reasoning": "Brief explanation of the reasoning.",
  "recommendation": {{
    "action": "pit_stop",
    "target_lap": 20,
    "tyre_compound": "medium",
    "confidence": 0.90,
    "rationale": "Brief strategic rationale.",
    "alternative_action": null
  }}
}}

Allowed category values:
tyre_strategy,
race_strategy,
weather,
mechanical,
safety,
position,
other

Allowed urgency values:
low,
medium,
high,
critical

Allowed action values:
pit_stop,
stay_out,
push,
manage_tyres,
defend,
attack,
no_action

Allowed tyre_compound values:
soft,
medium,
hard,
intermediate,
wet

Confidence values must be between 0.0 and 1.0.
target_lap must be an integer greater than or equal to 1,
or null.
tyre_compound may be null.
alternative_action may be null.

Do not include markdown or any text outside the JSON.
""".strip()

    # ======================================================================
    # RESPONSE → DOMAIN
    # ======================================================================

    def _build_analysis(
        self,
        *,
        parsed_result: dict,
        data: dict,
        start_time: float,
    ) -> AIAnalysis:
        """
        Convierte la respuesta JSON de Ollama en AIAnalysis.

        Aquí se produce la transformación entre la respuesta
        externa del provider y el modelo de dominio de ARXIA.
        """
        recommendation_data = parsed_result["recommendation"]

        recommendation = Recommendation(
            action=recommendation_data["action"],
            target_lap=recommendation_data.get("target_lap"),
            tyre_compound=recommendation_data.get("tyre_compound"),
            confidence=recommendation_data["confidence"],
            rationale=recommendation_data["rationale"],
            alternative_action=recommendation_data.get(
                "alternative_action"
            ),
        )

        # Ollama proporciona el número de tokens utilizados
        # mediante estas dos propiedades.
        input_tokens = data.get(
            "prompt_eval_count",
            0,
        )

        output_tokens = data.get(
            "eval_count",
            0,
        )

        total_tokens = input_tokens + output_tokens

        # Medimos la latencia completa de la operación.
        latency_ms = (
            time.perf_counter() - start_time
        ) * 1000

        metrics = ModelMetrics(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total_tokens,
            latency_ms=latency_ms,
            cost=0.0,
            retries=0,
        )

        return AIAnalysis(
            # TEMPORAL:
            # Provider todavía no dispone de OLLAMA.
            provider=Provider.OLLAMA,
            model=self.model,
            status=AnalysisStatus.SUCCESS,
            category=parsed_result["category"],
            urgency=parsed_result["urgency"],
            confidence=parsed_result["confidence"],
            summary=parsed_result["summary"],
            reasoning=parsed_result["reasoning"],
            recommendation=recommendation,
            metrics=metrics,
            error=None,
        )

    # ======================================================================
    # ERROR HANDLING
    # ======================================================================

    def _build_error_analysis(
        self,
        *,
        error: str,
        start_time: float,
    ) -> AIAnalysis:
        """
        Construye un AIAnalysis de error.

        ARXIA no debe romper el pipeline simplemente porque un
        provider externo falle.

        En su lugar, devuelve un análisis explícitamente marcado
        como ERROR para que posteriormente el RiskEngine y el
        DecisionEngine puedan reaccionar de forma determinista.
        """
        latency_ms = (
            time.perf_counter() - start_time
        ) * 1000

        metrics = ModelMetrics(
            input_tokens=0,
            output_tokens=0,
            total_tokens=0,
            latency_ms=latency_ms,
            cost=0.0,
            retries=0,
        )

        return AIAnalysis(
            # TEMPORAL:
            # Provider todavía no dispone de OLLAMA.
            provider=Provider.OLLAMA,
            model=self.model,
            status=AnalysisStatus.ERROR,
            category=AnalysisCategory.OTHER,
            urgency=AnalysisUrgency.CRITICAL,
            confidence=0.0,
            summary="Ollama provider failed to produce an analysis.",
            reasoning="The local model provider returned an error.",
            recommendation=Recommendation(
                action=RecommendationAction.NO_ACTION,
                target_lap=None,
                tyre_compound=None,
                confidence=0.0,
                rationale=(
                    "No recommendation available because "
                    "the provider failed."
                ),
                alternative_action=None,
            ),
            metrics=metrics,
            error=error,
        )