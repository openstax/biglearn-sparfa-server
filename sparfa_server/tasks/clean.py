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
            ecosystem_matrix_uuids = session.query(EcosystemMatrix.uuid).filter(
                EcosystemMatrix.superseded_by_uuid.isnot(None),
                EcosystemMatrix.is_used_in_assignments.is_(False),
                EcosystemMatrix.updated_at <= datetime.now() - CLEANUP_AFTER
            ).with_for_update(skip_locked=True).limit(BATCH_SIZE).all()

            session.query(EcosystemMatrix).filter(
                EcosystemMatrix.uuid.in_(ecosystem_matrix_uuids)
            ).delete(synchronize_session=False)

            if len(ecosystem_matrix_uuids) < BATCH_SIZE:
                break
