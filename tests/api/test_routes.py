import pytest
from fastapi.testclient import TestClient

from api.main import app
from api import routes
from core.domain.schemas import RaceEvent


client = TestClient(app)


# ============================================================================
# HELPERS
# ============================================================================


def build_race_event_payload() -> dict:
    """Construye un evento válido para las pruebas HTTP."""

    return {
        "circuit": "Monza",
        "session": "race",
        "lap": 20,
        "driver": "Test Driver",
        "team": "Test Team",
        "position": 5,
        "event_type": "strategic_opportunity",
        "description": "Strategic opportunity detected during the race.",
    }


# ============================================================================
# HEALTH CHECK
# ============================================================================


def test_health_check_returns_expected_response():
    """El endpoint raíz debe indicar que ARXIA está disponible."""

    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {
        "application": "ARXIA",
        "status": "running",
        "architecture": "gemini_vs_ollama",
    }


# ============================================================================
# CORE FACTORY
# ============================================================================


def test_create_arxia_core_uses_mock_providers_by_default(monkeypatch):
    """Por defecto ARXIA debe utilizar los proveedores mock."""

    monkeypatch.delenv(
        "ARXIA_PROVIDER_MODE",
        raising=False,
    )

    core = routes.create_arxia_core()

    assert isinstance(
        core.gemini_provider,
        routes.MockGeminiProvider,
    )

    assert isinstance(
        core.ollama_provider,
        routes.MockOllamaProvider,
    )


def test_create_arxia_core_uses_mock_providers_when_configured(
    monkeypatch,
):
    """El modo mock debe crear los proveedores simulados."""

    monkeypatch.setenv(
        "ARXIA_PROVIDER_MODE",
        "mock",
    )

    core = routes.create_arxia_core()

    assert isinstance(
        core.gemini_provider,
        routes.MockGeminiProvider,
    )

    assert isinstance(
        core.ollama_provider,
        routes.MockOllamaProvider,
    )


def test_create_arxia_core_accepts_uppercase_provider_mode(
    monkeypatch,
):
    """El modo de proveedores debe ser independiente de mayúsculas."""

    monkeypatch.setenv(
        "ARXIA_PROVIDER_MODE",
        "MOCK",
    )

    core = routes.create_arxia_core()

    assert isinstance(
        core.gemini_provider,
        routes.MockGeminiProvider,
    )

    assert isinstance(
        core.ollama_provider,
        routes.MockOllamaProvider,
    )


def test_create_arxia_core_rejects_unsupported_provider_mode(
    monkeypatch,
):
    """Un modo de proveedores desconocido debe producir ValueError."""

    monkeypatch.setenv(
        "ARXIA_PROVIDER_MODE",
        "unsupported",
    )

    with pytest.raises(
        ValueError,
        match="Modo de proveedores no soportado",
    ):
        routes.create_arxia_core()


# ============================================================================
# ANALYZE ENDPOINT
# ============================================================================


def test_analyze_endpoint_returns_arxia_result(monkeypatch):
    """El endpoint /analyze debe devolver el resultado completo de ARXIA."""

    original_core = routes.arxia_core

    class FakeArxiaCore:
        def process(self, race_event: RaceEvent):
            assert race_event.circuit == "Monza"
            assert race_event.lap == 20

            return original_core.process(race_event)

    monkeypatch.setattr(
        routes,
        "arxia_core",
        FakeArxiaCore(),
    )

    response = client.post(
        "/analyze",
        json=build_race_event_payload(),
    )

    assert response.status_code == 200

    body = response.json()

    assert "race_event" in body
    assert "gemini_analysis" in body
    assert "ollama_analysis" in body
    assert "comparison" in body
    assert "risk_assessment" in body
    assert "decision" in body


def test_analyze_endpoint_passes_race_event_to_core(monkeypatch):
    """El endpoint debe convertir el JSON y pasar el RaceEvent al core."""

    original_core = routes.arxia_core
    captured = {}

    class FakeArxiaCore:
        def process(self, race_event: RaceEvent):
            captured["race_event"] = race_event

            return original_core.process(race_event)

    monkeypatch.setattr(
        routes,
        "arxia_core",
        FakeArxiaCore(),
    )

    response = client.post(
        "/analyze",
        json=build_race_event_payload(),
    )

    assert response.status_code == 200

    event = captured["race_event"]

    assert isinstance(event, RaceEvent)
    assert event.circuit == "Monza"
    assert event.session.value == "race"
    assert event.lap == 20
    assert event.driver == "Test Driver"
    assert event.team == "Test Team"
    assert event.position == 5


def test_analyze_endpoint_rejects_invalid_race_event():
    """El endpoint debe rechazar eventos que no cumplen RaceEvent."""

    payload = build_race_event_payload()
    payload["lap"] = 0

    response = client.post(
        "/analyze",
        json=payload,
    )

    assert response.status_code == 422


def test_analyze_endpoint_rejects_missing_required_fields():
    """El endpoint debe rechazar requests incompletos."""

    response = client.post(
        "/analyze",
        json={
            "circuit": "Monza",
        },
    )

    assert response.status_code == 422


def test_analyze_endpoint_converts_core_exception_to_http_500(
    monkeypatch,
):
    """Una excepción del core debe convertirse en HTTP 500."""

    class FailingArxiaCore:
        def process(self, race_event: RaceEvent):
            raise RuntimeError("Core unavailable")

    monkeypatch.setattr(
        routes,
        "arxia_core",
        FailingArxiaCore(),
    )

    response = client.post(
        "/analyze",
        json=build_race_event_payload(),
    )

    assert response.status_code == 500
    assert response.json() == {
        "detail": (
            "Error procesando el evento con ARXIA: "
            "Core unavailable"
        )
    }