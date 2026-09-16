"""
Rutas HTTP de SIGNA.
"""

import os

from fastapi import APIRouter, HTTPException

from application.signa_core import SignaCore
from core.domain.schemas import Incident, TriageResult
from infrastructure.mocks import (
    MockCloudProvider,
    MockLocalProvider,
)

router = APIRouter()


@router.get("/")
def health_check() -> dict[str, str]:
    """Comprueba que la API de SIGNA está disponible."""

    return {
        "application": "SIGNA",
        "status": "running",
    }


def create_signa_core() -> SignaCore:
    """
    Crea SIGNA Core utilizando los proveedores configurados.

    Por defecto se utilizan mocks para que la API pueda ejecutarse
    rápidamente durante el desarrollo.
    """

    provider_mode = os.getenv(
        "SIGNA_PROVIDER_MODE",
        "mock",
    ).lower()

    if provider_mode == "mock":
        return SignaCore(
            local_provider=MockLocalProvider(),
            cloud_provider=MockCloudProvider(),
        )

    raise ValueError(
        f"Modo de proveedores no soportado: {provider_mode}"
    )


signa_core = create_signa_core()


@router.post(
    "/triage",
    response_model=TriageResult,
)
def triage_incident(incident: Incident) -> TriageResult:
    """
    Recibe una incidencia y ejecuta el flujo completo de SIGNA.
    """

    try:
        return signa_core.triage(incident)

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Error procesando la incidencia: {exc}",
        ) from exc