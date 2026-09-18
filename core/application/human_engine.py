"""
Motor de revisión humana de ARXIA.

Gestiona las revisiones humanas generadas cuando ARXIA no puede
tomar una decisión automática de forma segura.

El motor es determinista y no depende de ningún proveedor de IA.
"""

from datetime import datetime, timezone

from core.domain.enums import DecisionType, ReviewStatus
from core.domain.schemas import (
    ArxiaDecision,
    HumanReview,
    Recommendation,
)


class HumanEngine:
    """Gestiona el ciclo de revisión humana de ARXIA."""

    # ==================================================================
    # CREAR REVISIÓN
    # ==================================================================

    @staticmethod
    def create_review(
        decision: ArxiaDecision,
    ) -> HumanReview:
        """
        Crea una revisión humana pendiente.

        La decisión generada por ARXIA se mantiene como propuesta.
        No se considera una decisión final hasta que un revisor
        humano complete la revisión.
        """

        if decision.decision != DecisionType.HUMAN_REVIEW:
            raise ValueError(
                "Human review can only be created for "
                "human-review decisions"
            )

        return HumanReview(
            status=ReviewStatus.PENDING,
            final_decision=None,
            reviewer_comment=None,
            reviewed_at=None,
        )

    # ==================================================================
    # COMPLETAR REVISIÓN
    # ==================================================================

    @staticmethod
    def complete_review(
        review: HumanReview,
        final_decision: Recommendation,
        reviewer_comment: str | None = None,
    ) -> HumanReview:
        """
        Completa una revisión humana.

        Args:
            review:
                Revisión humana pendiente.

            final_decision:
                Decisión final seleccionada por el revisor.

            reviewer_comment:
                Comentario opcional del revisor.

        Returns:
            HumanReview actualizado con estado completado.
        """

        if review.status != ReviewStatus.PENDING:
            raise ValueError(
                "Human review is not pending"
            )

        return review.model_copy(
            update={
                "status": ReviewStatus.COMPLETED,
                "final_decision": final_decision,
                "reviewer_comment": reviewer_comment,
                "reviewed_at": datetime.now(
                    timezone.utc
                ),
            }
        )