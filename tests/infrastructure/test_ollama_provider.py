"""
Tests para OllamaProvider.

Los tests simulan las respuestas de la API de Ollama para
evitar depender de un servidor Ollama real durante la ejecución
de la suite de tests.
"""

import json
from unittest.mock import Mock, patch

import requests

from domain.enums import (
    AnalysisCategory,
    AnalysisStatus,
    AnalysisUrgency,
    EventType,
    Provider,
    RecommendationAction,
    RaceSession,
    TyreCompound,
    WeatherCondition,
)
from domain.schemas import RaceEvent, WeatherData
from infrastructure.ollama_provider import OllamaProvider


class TestOllamaProvider:
    """Tests del proveedor de modelos basado en Ollama."""

    def test_analyze_success(self):
        """
        Verifica que una respuesta válida de Ollama produzca
        correctamente un AIAnalysis con estado SUCCESS.
        """

        provider = OllamaProvider()

        ollama_result = {
            "category": "race_strategy",
            "urgency": "medium",
            "confidence": 0.90,
            "summary": "Pit stop recommended.",
            "reasoning": "Tyre degradation is increasing.",
            "recommendation": {
                "action": "pit_stop",
                "target_lap": 20,
                "tyre_compound": "medium",
                "confidence": 0.90,
                "rationale": (
                    "A medium tyre provides a better race balance."
                ),
                "alternative_action": "stay_out",
            },
        }

        mock_response = Mock()

        mock_response.json.return_value = {
            "response": json.dumps(ollama_result),
            "prompt_eval_count": 100,
            "eval_count": 50,
        }

        with patch(
            "infrastructure.ollama_provider.requests.post",
            return_value=mock_response,
        ) as mock_post:
            race_event = self._build_race_event()

            result = provider.analyze(race_event)

        # Verificamos que se haya realizado una única petición
        # a la API de Ollama.
        mock_post.assert_called_once()

        # Verificamos el estado general del análisis.
        assert result.status == AnalysisStatus.SUCCESS

        # Ollama utiliza temporalmente Provider.GPT.
        assert result.provider == Provider.GPT
        assert result.model == "llama3.2:3b"

        # Verificamos los campos principales del análisis.
        assert result.category == AnalysisCategory.RACE_STRATEGY
        assert result.urgency == AnalysisUrgency.MEDIUM
        assert result.confidence == 0.90

        # Verificamos la recomendación generada.
        assert (
            result.recommendation.action
            == RecommendationAction.PIT_STOP
        )

        assert result.recommendation.target_lap == 20

        assert (
            result.recommendation.tyre_compound
            == TyreCompound.MEDIUM
        )

        assert (
            result.recommendation.alternative_action
            == RecommendationAction.STAY_OUT
        )

        # Verificamos las métricas devueltas por Ollama.
        assert result.metrics.input_tokens == 100
        assert result.metrics.output_tokens == 50
        assert result.metrics.total_tokens == 150
        assert result.metrics.cost == 0.0
        assert result.metrics.retries == 0

        # Una ejecución correcta no debe contener error.
        assert result.error is None

    def test_analyze_empty_response(self):
        """
        Verifica que una respuesta vacía de Ollama produzca
        un AIAnalysis con estado ERROR.
        """

        provider = OllamaProvider()

        mock_response = Mock()

        mock_response.json.return_value = {
            "response": "",
        }

        with patch(
            "infrastructure.ollama_provider.requests.post",
            return_value=mock_response,
        ):
            race_event = self._build_race_event()

            result = provider.analyze(race_event)

        # La respuesta vacía debe convertirse en ERROR.
        assert result.status == AnalysisStatus.ERROR

        assert result.provider == Provider.GPT
        assert result.confidence == 0.0

        # Cuando el provider falla no debe recomendar ninguna acción.
        assert (
            result.recommendation.action
            == RecommendationAction.NO_ACTION
        )

        assert result.error == (
            "Ollama returned an empty response"
        )

    def test_analyze_invalid_json(self):
        """
        Verifica que una respuesta que no contiene JSON válido
        produzca un AIAnalysis con estado ERROR.
        """

        provider = OllamaProvider()

        mock_response = Mock()

        mock_response.json.return_value = {
            "response": "this is not valid json",
        }

        with patch(
            "infrastructure.ollama_provider.requests.post",
            return_value=mock_response,
        ):
            race_event = self._build_race_event()

            result = provider.analyze(race_event)

        # El JSON inválido debe convertirse en ERROR.
        assert result.status == AnalysisStatus.ERROR

        assert result.confidence == 0.0

        assert (
            result.recommendation.action
            == RecommendationAction.NO_ACTION
        )

        assert result.error is not None
        assert "Invalid Ollama response" in result.error

    def test_analyze_connection_error(self):
        """
        Verifica que un error de conexión con Ollama no rompa
        el pipeline y produzca un AIAnalysis con estado ERROR.
        """

        provider = OllamaProvider()

        with patch(
            "infrastructure.ollama_provider.requests.post",
            side_effect=requests.ConnectionError(
                "Ollama is not running"
            ),
        ):
            race_event = self._build_race_event()

            result = provider.analyze(race_event)

        # Un fallo de conexión debe convertirse en ERROR.
        assert result.status == AnalysisStatus.ERROR

        assert result.provider == Provider.GPT
        assert result.confidence == 0.0

        assert (
            result.recommendation.action
            == RecommendationAction.NO_ACTION
        )

        assert "Ollama is not running" in result.error

    def test_analyze_http_error(self):
        """
        Verifica que un error HTTP de Ollama produzca
        correctamente un AIAnalysis con estado ERROR.
        """

        provider = OllamaProvider()

        mock_response = Mock()

        # Simulamos que Ollama responde con un error HTTP.
        mock_response.raise_for_status.side_effect = (
            requests.HTTPError("500 Server Error")
        )

        with patch(
            "infrastructure.ollama_provider.requests.post",
            return_value=mock_response,
        ):
            race_event = self._build_race_event()

            result = provider.analyze(race_event)

        # El error HTTP debe convertirse en ERROR.
        assert result.status == AnalysisStatus.ERROR

        assert result.confidence == 0.0

        assert (
            result.recommendation.action
            == RecommendationAction.NO_ACTION
        )

        assert "500 Server Error" in result.error

    def test_build_prompt_contains_race_event_data(self):
        """
        Verifica que el prompt contiene los datos principales
        del RaceEvent recibido.
        """

        provider = OllamaProvider()

        race_event = self._build_race_event()

        prompt = provider._build_prompt(race_event)

        # Comprobamos que el contexto principal de la carrera
        # haya sido incluido en el prompt.
        assert race_event.circuit in prompt
        assert race_event.driver in prompt
        assert race_event.team in prompt
        assert race_event.description in prompt

        assert str(race_event.lap) in prompt
        assert str(race_event.position) in prompt

        # Comprobamos que el prompt contiene las instrucciones
        # necesarias para obtener una respuesta JSON.
        assert (
            "Analyze the following motorsport race event."
            in prompt
        )

        assert "Return ONLY valid JSON" in prompt

    @staticmethod
    def _build_race_event() -> RaceEvent:
        """
        Construye un RaceEvent válido para utilizarlo
        en los diferentes tests del proveedor.
        """

        weather = WeatherData(
            condition=WeatherCondition.DRY,
            temperature_c=25.0,
            track_temperature_c=35.0,
            rain_probability=0.10,
            wind_speed_kmh=15.0,
        )

        return RaceEvent(
            circuit="Monza",
            session=RaceSession.RACE,
            lap=15,
            driver="Charles Leclerc",
            team="Ferrari",
            position=3,
            weather=weather,
            event_type=EventType.TYRE_DEGRADATION,
            tyre_compound=TyreCompound.MEDIUM,
            track_condition=WeatherCondition.DRY,
            race_context=(
                "The driver is fighting for a podium position."
            ),
            description=(
                "Tyre degradation is increasing on the current stint."
            ),
        )