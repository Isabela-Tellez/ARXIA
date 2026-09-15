from types import SimpleNamespace

import pytest

from domain.enums import (
    AnalysisCategory,
    AnalysisStatus,
    AnalysisUrgency,
    Provider,
    RecommendationAction,
    TyreCompound,
)
from domain.schemas import RaceEvent

from infrastructure.gemini_provider import (
    GeminiAnalysisResponse,
    GeminiProvider,
    GeminiRecommendation,
)


# ============================================================================
# HELPERS
# ============================================================================


def build_race_event() -> RaceEvent:
    """Crea un evento de carrera válido utilizado por los tests."""

    return RaceEvent(
        circuit="Monaco",
        session="race",
        lap=20,
        driver="Test Driver",
        team="Test Team",
        position=5,
        event_type="strategic_opportunity",
        description="Strategic opportunity detected during the race.",
    )


def build_gemini_response() -> GeminiAnalysisResponse:
    """Crea una respuesta estructurada válida para Gemini."""

    return GeminiAnalysisResponse(
        category=AnalysisCategory.RACE_STRATEGY,
        urgency=AnalysisUrgency.MEDIUM,
        confidence=0.95,
        summary="Strategic opportunity detected.",
        reasoning="A pit stop window is currently favorable.",
        recommendation=GeminiRecommendation(
            action=RecommendationAction.PIT_STOP,
            target_lap=20,
            tyre_compound=TyreCompound.MEDIUM,
            confidence=0.92,
            rationale=(
                "Pit stop is recommended to exploit the strategic window."
            ),
        ),
    )


def build_provider() -> GeminiProvider:
    """Crea un proveedor con una configuración determinista para tests."""

    return GeminiProvider(
        api_key="test-api-key",
        model="test-gemini-model",
    )


def build_mock_response() -> SimpleNamespace:
    """
    Crea una respuesta simulada compatible con la respuesta del SDK.

    Solo se incluyen los atributos que necesita el proveedor:
    respuesta estructurada, texto de respuesta y metadatos de tokens.
    """

    parsed = build_gemini_response()

    return SimpleNamespace(
        parsed=parsed,
        text=parsed.model_dump_json(),
        usage_metadata=SimpleNamespace(
            prompt_token_count=100,
            candidates_token_count=50,
        ),
    )


# ============================================================================
# INICIALIZACIÓN
# ============================================================================


def test_provider_requires_api_key(monkeypatch):
    """El proveedor debe rechazar la inicialización sin API key."""

    # Eliminamos la variable de entorno para comprobar que el proveedor
    # no puede iniciarse sin una configuración de autenticación válida.
    monkeypatch.delenv(
        "GEMINI_API_KEY",
        raising=False,
    )

    with pytest.raises(
        ValueError,
        match="GEMINI_API_KEY is required",
    ):
        GeminiProvider()


def test_provider_reads_api_key_from_environment(monkeypatch):
    """El proveedor debe poder obtener la API key desde el entorno."""

    # Simulamos la configuración utilizada normalmente en ejecución
    # sin utilizar una API key real de Gemini.
    monkeypatch.setenv(
        "GEMINI_API_KEY",
        "environment-api-key",
    )

    provider = GeminiProvider(
        model="test-model",
    )

    assert provider.api_key == "environment-api-key"
    assert provider.model == "test-model"


def test_provider_accepts_explicit_api_key():
    """El proveedor debe aceptar una API key proporcionada explícitamente."""

    provider = GeminiProvider(
        api_key="explicit-api-key",
        model="test-model",
    )

    assert provider.api_key == "explicit-api-key"
    assert provider.model == "test-model"


def test_provider_rejects_empty_model():
    """El proveedor debe rechazar un nombre de modelo vacío."""

    with pytest.raises(
        ValueError,
        match="Gemini model cannot be empty",
    ):
        GeminiProvider(
            api_key="test-api-key",
            model=" ",
        )


# ============================================================================
# PROMPT
# ============================================================================


def test_prompt_contains_race_event_context():
    """
    El prompt generado debe contener el contexto relevante de la carrera.

    Esto garantiza que Gemini recibe la información necesaria para
    analizar la situación actual de carrera.
    """

    provider = build_provider()

    prompt = provider._build_prompt(
        build_race_event(),
    )

    assert "Monaco" in prompt
    assert "Test Driver" in prompt
    assert "Test Team" in prompt
    assert "Lap: 20" in prompt
    assert "Position: 5" in prompt
    assert "strategic_opportunity" in prompt


# ============================================================================
# RESPUESTA EXITOSA
# ============================================================================


def test_gemini_provider_returns_valid_analysis(monkeypatch):
    """Una respuesta válida de Gemini debe convertirse en un AIAnalysis exitoso."""

    provider = build_provider()
    response = build_mock_response()

    def fake_generate_content(**kwargs):
        # Comprobamos que se utiliza el modelo configurado y que el
        # prompt contiene el contexto de la carrera.
        assert kwargs["model"] == "test-gemini-model"
        assert "Monaco" in kwargs["contents"]

        return response

    monkeypatch.setattr(
        provider.client.models,
        "generate_content",
        fake_generate_content,
    )

    result = provider.analyze(
        build_race_event(),
    )

    assert result.provider == Provider.GEMINI
    assert result.model == "test-gemini-model"
    assert result.status == AnalysisStatus.SUCCESS
    assert result.error is None


def test_gemini_provider_maps_recommendation(monkeypatch):
    """La recomendación estructurada de Gemini debe mapearse al dominio."""

    provider = build_provider()

    # Utilizamos una respuesta determinista para comprobar únicamente
    # la conversión entre el modelo de Gemini y el schema del dominio.
    monkeypatch.setattr(
        provider.client.models,
        "generate_content",
        lambda **kwargs: build_mock_response(),
    )

    result = provider.analyze(
        build_race_event(),
    )

    assert result.recommendation.action == (
        RecommendationAction.PIT_STOP
    )

    assert result.recommendation.target_lap == 20

    assert result.recommendation.tyre_compound == (
        TyreCompound.MEDIUM
    )

    assert result.recommendation.confidence == 0.92


def test_gemini_provider_maps_analysis_fields(monkeypatch):
    """Los campos principales de Gemini deben conservarse correctamente."""

    provider = build_provider()

    # Comprobamos que la respuesta estructurada se transforma en el
    # AIAnalysis utilizado por el resto de ARXIA.
    monkeypatch.setattr(
        provider.client.models,
        "generate_content",
        lambda **kwargs: build_mock_response(),
    )

    result = provider.analyze(
        build_race_event(),
    )

    assert result.category == AnalysisCategory.RACE_STRATEGY
    assert result.urgency == AnalysisUrgency.MEDIUM
    assert result.confidence == 0.95
    assert result.summary == "Strategic opportunity detected."


def test_gemini_provider_maps_usage_metrics(monkeypatch):
    """Los metadatos de uso de Gemini deben convertirse en ModelMetrics."""

    provider = build_provider()

    # Los tokens proceden de la respuesta simulada del SDK y permiten
    # comprobar que las métricas llegan correctamente al dominio.
    monkeypatch.setattr(
        provider.client.models,
        "generate_content",
        lambda **kwargs: build_mock_response(),
    )

    result = provider.analyze(
        build_race_event(),
    )

    assert result.metrics.input_tokens == 100
    assert result.metrics.output_tokens == 50
    assert result.metrics.total_tokens == 150
    assert result.metrics.latency_ms >= 0
    assert result.metrics.cost >= 0
    assert result.metrics.retries >= 0


# ============================================================================
# RESPUESTA INVÁLIDA
# ============================================================================


def test_gemini_provider_returns_invalid_status_for_invalid_response(
    monkeypatch,
):
    """
    Una respuesta sin datos estructurados debe marcarse como INVALID.

    Esto evita que respuestas incompletas o inutilizables de Gemini
    lleguen al resto del dominio.
    """

    provider = build_provider()

    invalid_response = SimpleNamespace(
        parsed=None,
        text='{"invalid": "response"}',
        usage_metadata=None,
    )

    monkeypatch.setattr(
        provider.client.models,
        "generate_content",
        lambda **kwargs: invalid_response,
    )

    result = provider.analyze(
        build_race_event(),
    )

    assert result.provider == Provider.GEMINI
    assert result.status == AnalysisStatus.INVALID
    assert result.error is not None


def test_gemini_provider_returns_invalid_status_for_empty_response(
    monkeypatch,
):
    """Una respuesta vacía de Gemini debe rechazarse como INVALID."""

    provider = build_provider()

    empty_response = SimpleNamespace(
        parsed=None,
        text="",
        usage_metadata=None,
    )

    monkeypatch.setattr(
        provider.client.models,
        "generate_content",
        lambda **kwargs: empty_response,
    )

    result = provider.analyze(
        build_race_event(),
    )

    assert result.status == AnalysisStatus.INVALID
    assert result.error is not None


# ============================================================================
# ERRORES
# ============================================================================


def test_gemini_provider_handles_timeout(monkeypatch):
    """Un timeout de Gemini debe producir un resultado TIMEOUT."""

    provider = build_provider()

    def fake_generate_content(**kwargs):
        # Simulamos un timeout producido durante la comunicación
        # con el servicio externo de Gemini.
        raise TimeoutError("request timed out")

    monkeypatch.setattr(
        provider.client.models,
        "generate_content",
        fake_generate_content,
    )

    result = provider.analyze(
        build_race_event(),
    )

    assert result.provider == Provider.GEMINI
    assert result.status == AnalysisStatus.TIMEOUT
    assert result.error == "Gemini request timed out."
    assert result.confidence == 0.0


def test_gemini_provider_handles_api_error(monkeypatch):
    """Un error inesperado del proveedor debe producir un resultado ERROR."""

    provider = build_provider()

    def fake_generate_content(**kwargs):
        # Simulamos una API externa no disponible.
        raise RuntimeError("API unavailable")

    monkeypatch.setattr(
        provider.client.models,
        "generate_content",
        fake_generate_content,
    )

    result = provider.analyze(
        build_race_event(),
    )

    assert result.provider == Provider.GEMINI
    assert result.status == AnalysisStatus.ERROR
    assert "API unavailable" in result.error
    assert result.confidence == 0.0


# ============================================================================
# CONTRATO DE ANÁLISIS CON ERROR
# ============================================================================


def test_failed_analysis_has_valid_error_contract(monkeypatch):
    """
    Un análisis fallido debe seguir cumpliendo el contrato de AIAnalysis.

    En particular, debe contener un error, tener confianza cero y
    utilizar NO_ACTION como recomendación segura.
    """

    provider = build_provider()

    # Simulamos un fallo del proveedor sin realizar ninguna llamada
    # al servicio real de Gemini.
    monkeypatch.setattr(
        provider.client.models,
        "generate_content",
        lambda **kwargs: (_ for _ in ()).throw(
            RuntimeError("Gemini unavailable")
        ),
    )

    result = provider.analyze(
        build_race_event(),
    )

    assert result.status == AnalysisStatus.ERROR
    assert result.error is not None
    assert result.recommendation.action == (
        RecommendationAction.NO_ACTION
    )
    assert result.recommendation.confidence == 0.0
    assert result.metrics.total_tokens == (
        result.metrics.input_tokens
        + result.metrics.output_tokens
    )