from uuid import uuid4
from datetime import datetime, timedelta

from sparfa_server.orm import Ecosystem, EcosystemMatrix
from sparfa_server.tasks.clean import cleanup_ecosystem_matrices


def test_cleanup_ecosystem_matrices(transaction):
    ecosystem_1 = Ecosystem(
      uuid=str(uuid4()),
      metadata_sequence_number=0,
      sequence_number=1,
      last_ecosystem_matrix_update_calculation_uuid=str(uuid4())
    )

    ecosystem_2 = Ecosystem(
      uuid=str(uuid4()),
      metadata_sequence_number=1,
      sequence_number=1,
      last_ecosystem_matrix_update_calculation_uuid=str(uuid4())
    )

    ecosystem_matrix_1 = EcosystemMatrix(
        uuid=str(uuid4()),
        ecosystem_uuid=ecosystem_1.uuid,
        Q_ids=[],
        C_ids=[],
        d_data=[],
        w_data=[],
        w_row=[],
        w_col=[],
        h_mask_data=[],
        h_mask_row=[],
        h_mask_col=[]
    )

    ecosystem_matrix_2 = EcosystemMatrix(
        uuid=str(uuid4()),
        ecosystem_uuid=ecosystem_1.uuid,
        superseded_by_uuid=ecosystem_matrix_1.uuid,
        Q_ids=[],
        C_ids=[],
        d_data=[],
        w_data=[],
        w_row=[],
        w_col=[],
        h_mask_data=[],
        h_mask_row=[],
        h_mask_col=[]
    )

    ecosystem_matrix_3 = EcosystemMatrix(
        uuid=str(uuid4()),
        ecosystem_uuid=ecosystem_2.uuid,
        Q_ids=[],
        C_ids=[],
        d_data=[],
        w_data=[],
        w_row=[],
        w_col=[],
        h_mask_data=[],
        h_mask_row=[],
        h_mask_col=[],
        created_at=datetime.now() - timedelta(days=30),
        updated_at=datetime.now() - timedelta(days=30)
    )

    ecosystem_matrix_4 = EcosystemMatrix(
        uuid=str(uuid4()),
        ecosystem_uuid=ecosystem_2.uuid,
        superseded_by_uuid=ecosystem_matrix_3.uuid,
        is_used_in_assignments=True,
        Q_ids=[],
        C_ids=[],
        d_data=[],
        w_data=[],
        w_row=[],
        w_col=[],
        h_mask_data=[],
        h_mask_row=[],
        h_mask_col=[],
        created_at=datetime.now() - timedelta(days=30),
        updated_at=datetime.now() - timedelta(days=30)
    )

    ecosystem_matrix_5 = EcosystemMatrix(
        uuid=str(uuid4()),
        ecosystem_uuid=ecosystem_2.uuid,
        superseded_by_uuid=ecosystem_matrix_3.uuid,
        is_used_in_assignments=False,
        Q_ids=[],
        C_ids=[],
        d_data=[],
        w_data=[],
        w_row=[],
        w_col=[],
        h_mask_data=[],
        h_mask_row=[],
        h_mask_col=[],
        created_at=datetime.now() - timedelta(days=30),
        updated_at=datetime.now() - timedelta(days=30)
    )

    with transaction() as session:
        assert not session.query(EcosystemMatrix).all()

        session.add(ecosystem_matrix_1)
        session.add(ecosystem_matrix_2)
        session.add(ecosystem_matrix_3)
        session.add(ecosystem_matrix_4)
        session.add(ecosystem_matrix_5)

    cleanup_ecosystem_matrices()

    with transaction() as session:
        ecosystem_matrices = set(
            session.query(EcosystemMatrix).order_by(EcosystemMatrix.created_at).all()
        )

    assert len(ecosystem_matrices) == 4
    assert ecosystem_matrix_1 in ecosystem_matrices
    assert ecosystem_matrix_2 in ecosystem_matrices
    assert ecosystem_matrix_3 in ecosystem_matrices
    assert ecosystem_matrix_4 in ecosystem_matrices
    assert ecosystem_matrix_5 not in ecosystem_matrices
