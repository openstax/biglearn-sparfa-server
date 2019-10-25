from datetime import timedelta, datetime

from ..orm import transaction, EcosystemMatrix
from .celery import task

CLEANUP_AFTER = timedelta(days=30)
BATCH_SIZE = 1000


@task
def cleanup_ecosystem_matrices():
    """Calculate old unused ecosystem matrices"""
    while True:
        with transaction() as session:
            ecosystem_matrices = session.query(EcosystemMatrix.uuid).filter(
                EcosystemMatrix.is_used_in_assignments.is_(False),
                EcosystemMatrix.superseded_at <= datetime.now() - CLEANUP_AFTER
            ).with_for_update(skip_locked=True).limit(BATCH_SIZE).all()

            if ecosystem_matrices:
                session.query(EcosystemMatrix).filter(
                    EcosystemMatrix.uuid.in_([matrix.uuid for matrix in ecosystem_matrices])
                ).delete(synchronize_session=False)

            if len(ecosystem_matrices) < BATCH_SIZE:
                break
