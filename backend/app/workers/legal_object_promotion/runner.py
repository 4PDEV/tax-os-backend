from sqlalchemy.orm import Session

from app.workers.legal_object_promotion.controlled_provider import (
    ControlledLegalObjectPromotionProvider,
)
from app.workers.legal_object_promotion.dry_run_provider import DryRunLegalObjectPromotionProvider
from app.workers.legal_object_promotion.result import LegalObjectPromotionRunSummary
from app.workers.legal_object_promotion.worker import (
    EXECUTION_MODE_CONTROLLED_PROMOTION,
    EXECUTION_MODE_DRY_RUN,
    LegalObjectPromotionWorker,
    LegalObjectPromotionWorkerError,
)


def run_legal_object_promotion_dry_run(
    db: Session,
    *,
    worker_name: str = "legal-object-promotion-worker",
    worker_version: str = "0.1.0",
    dry_run: bool = True,
) -> LegalObjectPromotionRunSummary:
    if not dry_run:
        raise LegalObjectPromotionWorkerError(
            "dry_run=True is required for run_legal_object_promotion_dry_run"
        )
    worker = LegalObjectPromotionWorker(
        provider=DryRunLegalObjectPromotionProvider(),
        mode=EXECUTION_MODE_DRY_RUN,
    )
    return worker.run(db, worker_name=worker_name, worker_version=worker_version)


def run_controlled_legal_object_promotion(
    db: Session,
    *,
    worker_name: str = "legal-object-promotion-worker",
    worker_version: str = "0.1.0",
    controlled_promotion: bool = True,
) -> LegalObjectPromotionRunSummary:
    if not controlled_promotion:
        raise LegalObjectPromotionWorkerError(
            "controlled_promotion=True is required for run_controlled_legal_object_promotion"
        )
    worker = LegalObjectPromotionWorker(
        provider=ControlledLegalObjectPromotionProvider(),
        mode=EXECUTION_MODE_CONTROLLED_PROMOTION,
    )
    return worker.run(db, worker_name=worker_name, worker_version=worker_version)
