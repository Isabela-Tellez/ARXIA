"""
Aplicación FastAPI de ARXIA.
"""

from fastapi import FastAPI

from api.routes import router

app = FastAPI(
title="ARXIA API",
description=(
"Motor de decisión multimodelo para análisis de eventos "
"de motorsport mediante Gemini y Ollama."
),
version="1.0.0",
)

app.include_router(router)