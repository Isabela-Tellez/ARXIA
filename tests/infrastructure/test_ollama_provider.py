import json
from types import SimpleNamespace

import pytest
import requests

from core.domain.enums import (
    AnalysisCategory,
    AnalysisStatus,
    AnalysisUrgency,
    Provider,
    RecommendationAction,
    TyreCompound,
)
from core.domain.schemas import RaceEvent
from infrastructure.ollama_provider import (
    OllamaAnalysisResponse,
    OllamaProvider,
    OllamaRecommendation,
)


# ============================================================================
# HELPERS
# ============================================================================


def build_race_event() -> RaceEvent:
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


def build_ollama_response() -> OllamaAnalysisResponse:
    return OllamaAnalysisResponse(
        category=AnalysisCategory.RACE_STRATEGY,
        urgency=AnalysisUrgency.MEDIUM,
        confidence=0.95,
        summary="Strategic opportunity detected.",
        reasoning="A pit stop window is currently favorable.",
        recommendation=OllamaRecommendation(
            action=RecommendationAction.PIT_STOP,
            target_lap=20,
            tyre_compound=TyreCompound.MEDIUM,
            confidence=0.92,
            rationale="Pit stop is recommended to exploit the strategic window.",
            alternative_action=RecommendationAction.STAY_OUT,
        ),
    )


def build_mock_http_response(**overrides) -> SimpleNamespace:
    data = {
        "response": build_ollama_response().model_dump_json(),
        "prompt_eval_count": 100,
        "eval_count": 50,
    }
    data.update(overrides)

    return SimpleNamespace(
        json=lambda: data,
        raise_for_status=lambda: None,
    )


def mock_post(monkeypatch, response=None):
    monkeypatch.setattr(
        "infrastructure.ollama_provider.requests.post",
        lambda *args, **kwargs: response or build_mock_http_response(),
    )


def mock_post_error(monkeypatch, error):
    monkeypatch.setattr(
        "infrastructure.ollama_provider.requests.post",
        lambda *args, **kwargs: (_ for _ in ()).throw(error),
    )


# ============================================================================
# INITIALIZATION
# ============================================================================


@pytest.mark.parametrize(
    ("attribute", "expected"),
    [
        ("model", "llama3.2:1b"),
        ("base_url", "http://localhost:11434"),
        ("timeout", 60.0),
        ("num_predict", 256),
    ],
)
def test_provider_defaults(attribute, expected):
    assert getattr(OllamaProvider(), attribute) == expected


def test_provider_accepts_custom_configuration():
    provider = OllamaProvider(
        model="custom-model",
        base_url="http://ollama.test/",
        timeout=30.0,
        num_predict=128,
    )

    assert provider.model == "custom-model"
    assert provider.base_url == "http://ollama.test"
    assert provider.timeout == 30.0
    assert provider.num_predict == 128


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        (
            {"model": " "},
            "Ollama model cannot be empty",
        ),
        (
            {"base_url": " "},
            "Ollama base URL cannot be empty",
        ),
        (
            {"timeout": 0},
            "Ollama timeout must be greater than zero",
        ),
        (
            {"num_predict": 0},
            "Ollama num_predict must be greater than zero",
        ),
    ],
)
def test_provider_rejects_invalid_configuration(kwargs, message):
    with pytest.raises(ValueError, match=message):
        OllamaProvider(**kwargs)


# ============================================================================
# PROMPT
# ============================================================================


def test_prompt_contains_race_event_context():
    prompt = OllamaProvider()._build_prompt(build_race_event())

    for value in (
        "Monaco",
        "Test Driver",
        "Test Team",
        "Lap: 20",
        "Position: 5",
        "strategic_opportunity",
    ):
        assert value in prompt


def test_prompt_requires_json_response():
    prompt = OllamaProvider()._build_prompt(build_race_event())
    assert "Return ONLY valid JSON" in prompt


# ============================================================================
# REQUEST
# ============================================================================


def test_provider_sends_expected_request_configuration(monkeypatch):
    provider = OllamaProvider(
        model="test-ollama-model",
        base_url="http://ollama.test",
        num_predict=128,
    )

    def fake_post(url, **kwargs):
        assert url == "http://ollama.test/api/generate"

        payload = kwargs["json"]

        assert payload["model"] == "test-ollama-model"
        assert payload["stream"] is False
        assert payload["format"] == "json"
        assert payload["options"] == {
            "temperature": 0,
            "num_predict": 128,
        }
        assert "Monaco" in payload["prompt"]
        assert kwargs["timeout"] == provider.timeout

        return build_mock_http_response()

    monkeypatch.setattr(
        "infrastructure.ollama_provider.requests.post",
        fake_post,
    )

    assert provider.analyze(build_race_event()).status == AnalysisStatus.SUCCESS


# ============================================================================
# SUCCESS
# ============================================================================


def test_ollama_provider_returns_valid_analysis(monkeypatch):
    provider = OllamaProvider(model="test-ollama-model")
    mock_post(monkeypatch)

    result = provider.analyze(build_race_event())

    assert result.provider == Provider.OLLAMA
    assert result.model == "test-ollama-model"
    assert result.status == AnalysisStatus.SUCCESS
    assert result.error is None


def test_ollama_provider_maps_analysis_and_recommendation(monkeypatch):
    mock_post(monkeypatch)

    result = OllamaProvider().analyze(build_race_event())
    rec = result.recommendation

    assert result.category == AnalysisCategory.RACE_STRATEGY
    assert result.urgency == AnalysisUrgency.MEDIUM
    assert result.confidence == 0.95
    assert result.summary == "Strategic opportunity detected."
    assert result.reasoning == "A pit stop window is currently favorable."

    assert rec.action == RecommendationAction.PIT_STOP
    assert rec.target_lap == 20
    assert rec.tyre_compound == TyreCompound.MEDIUM
    assert rec.confidence == 0.92
    assert rec.rationale == (
        "Pit stop is recommended to exploit the strategic window."
    )
    assert rec.alternative_action == RecommendationAction.STAY_OUT


# ============================================================================
# METRICS
# ============================================================================


def test_ollama_provider_maps_usage_metrics(monkeypatch):
    mock_post(monkeypatch)

    metrics = OllamaProvider().analyze(build_race_event()).metrics

    assert metrics.input_tokens == 100
    assert metrics.output_tokens == 50
    assert metrics.total_tokens == 150
    assert metrics.cost == 0.0
    assert metrics.retries == 0
    assert metrics.latency_ms >= 0


def test_total_tokens_equals_input_plus_output(monkeypatch):
    mock_post(monkeypatch)

    metrics = OllamaProvider().analyze(build_race_event()).metrics

    assert metrics.total_tokens == (
        metrics.input_tokens + metrics.output_tokens
    )


# ============================================================================
# INVALID RESPONSES
# ============================================================================


@pytest.mark.parametrize(
    "response",
    [
        build_mock_http_response(
            response=json.dumps({"invalid": "response"}),
            prompt_eval_count=0,
            eval_count=0,
        ),
        build_mock_http_response(
            response="",
            prompt_eval_count=0,
            eval_count=0,
        ),
        build_mock_http_response(response="{invalid}"),
        build_mock_http_response(
            response={"category": "race_strategy"},
        ),
    ],
)
def test_ollama_provider_handles_invalid_responses(monkeypatch, response):
    mock_post(monkeypatch, response)

    result = OllamaProvider().analyze(build_race_event())

    assert result.status == AnalysisStatus.INVALID
    assert result.error is not None
    assert result.confidence == 0.0


def test_invalid_json_error_is_descriptive(monkeypatch):
    mock_post(
        monkeypatch,
        build_mock_http_response(response="{invalid}"),
    )

    result = OllamaProvider().analyze(build_race_event())

    assert result.status == AnalysisStatus.INVALID
    assert "invalid JSON" in result.error


# ============================================================================
# ERRORS
# ============================================================================


def test_ollama_provider_handles_timeout(monkeypatch):
    mock_post_error(
        monkeypatch,
        requests.Timeout("timed out"),
    )

    result = OllamaProvider().analyze(build_race_event())

    assert result.status == AnalysisStatus.TIMEOUT
    assert result.error == "Ollama request timed out."
    assert result.confidence == 0.0


@pytest.mark.parametrize(
    "error",
    [
        requests.HTTPError("500 Server Error"),
        requests.ConnectionError("unavailable"),
        RuntimeError("Unexpected failure"),
    ],
)
def test_ollama_provider_handles_errors(monkeypatch, error):
    mock_post_error(monkeypatch, error)

    result = OllamaProvider().analyze(build_race_event())

    assert result.status == AnalysisStatus.ERROR
    assert str(error) in result.error
    assert result.confidence == 0.0


def test_failed_analysis_has_valid_error_contract(monkeypatch):
    mock_post_error(
        monkeypatch,
        requests.ConnectionError(),
    )

    result = OllamaProvider().analyze(build_race_event())

    assert result.status == AnalysisStatus.ERROR
    assert result.recommendation.action == RecommendationAction.NO_ACTION
    assert result.recommendation.confidence == 0.0
    assert result.metrics.total_tokens == (
        result.metrics.input_tokens
        + result.metrics.output_tokens
    )


# ============================================================================
# RESPONSE PARSING
# ============================================================================


def test_parse_response_returns_structured_response():
    result = OllamaProvider()._parse_response(
        build_mock_http_response()
    )

    assert isinstance(result, OllamaAnalysisResponse)
    assert result.category == AnalysisCategory.RACE_STRATEGY
    assert result.urgency == AnalysisUrgency.MEDIUM
    assert result.recommendation.action == RecommendationAction.PIT_STOP
    assert result.recommendation.alternative_action == (
        RecommendationAction.STAY_OUT
    )


def test_parse_response_rejects_invalid_http_json():
    response = SimpleNamespace(
        json=lambda: (_ for _ in ()).throw(ValueError())
    )

    with pytest.raises(
        ValueError,
        match="Ollama returned invalid HTTP JSON",
    ):
        OllamaProvider()._parse_response(response)


def test_parse_response_rejects_empty_model_response():
    response = SimpleNamespace(
        json=lambda: {"response": ""}
    )

    with pytest.raises(
        ValueError,
        match="Ollama returned an empty response",
    ):
        OllamaProvider()._parse_response(response)