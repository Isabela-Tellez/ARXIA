from fastapi import FastAPI

from api.main import app


def test_app_is_fastapi_instance():
    """La aplicación ARXIA debe ser una instancia de FastAPI."""

    assert isinstance(app, FastAPI)


def test_app_metadata_is_configured():
    """La aplicación debe exponer la metadata esperada."""

    assert app.title == "ARXIA API"
    assert (
        app.description
        == (
            "Motor de decisión multimodelo para análisis de eventos "
            "de motorsport mediante Gemini y Ollama."
        )
    )
    assert app.version == "1.0.0"