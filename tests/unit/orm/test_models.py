from uuid import uuid4
from random import choice
from datetime import datetime

from numpy import array

from sparfa_server.orm.models import Ecosystem, BaseBase, Response, EcosystemMatrix, Page


class TestBaseBase(object):
    def test_dict(self):
        ecosystem = Ecosystem(uuid=uuid4(), sequence_number=1)
        assert isinstance(ecosystem, BaseBase)
        assert ecosystem.dict == {
            'uuid': ecosystem.uuid, 'sequence_number': ecosystem.sequence_number
        }


class TestResponse(object):
    def test_dict_for_algs(self):
        response = Response(
            student_uuid=uuid4(),
            exercise_uuid=uuid4(),
            is_correct=choice((True, False)),
            responded_at=datetime.now()
        )
        assert response.dict_for_algs == {
            'L_id':         str(response.student_uuid),
            'Q_id':         str(response.exercise_uuid),
            'correct?':     response.is_correct,
            'responded_at': str(response.responded_at)
        }


class TestEcosystemMatrix(object):
    def test_NC(self):
        ecosystem_matrix = EcosystemMatrix(C_ids=[uuid4(), uuid4(), uuid4()])
        assert ecosystem_matrix.NC == len(ecosystem_matrix.C_ids)

    def test_NQ(self):
        ecosystem_matrix = EcosystemMatrix(Q_ids=[uuid4(), uuid4(), uuid4()])
        assert ecosystem_matrix.NQ == len(ecosystem_matrix.Q_ids)

    def test_W_NCxNQ(self):
        w_ncxnq = array(((0.0, 0.5, 1.0), (1.0, 0.5, 0.0)))
        ecosystem_matrix = EcosystemMatrix(
            C_ids=[uuid4(), uuid4()],
            Q_ids=[uuid4(), uuid4(), uuid4()],
            W_NCxNQ=w_ncxnq
        )
        assert (ecosystem_matrix.W_NCxNQ == w_ncxnq).all()

    def test_H_mask_NCxNQ(self):
        h_mask_nc_nq = array(((False, True, True), (True, True, False)))
        ecosystem_matrix = EcosystemMatrix(
            C_ids=[uuid4(), uuid4()],
            Q_ids=[uuid4(), uuid4(), uuid4()],
            H_mask_NCxNQ=h_mask_nc_nq
        )
        assert (ecosystem_matrix.H_mask_NCxNQ == h_mask_nc_nq).all()

    def test_d_NQx1(self):
        d_nqx1 = array(((1.0,), (0.5,), (0.0,)))
        ecosystem_matrix = EcosystemMatrix(d_NQx1=d_nqx1)
        assert (ecosystem_matrix.d_NQx1 == d_nqx1).all()

    def test_response_dicts_for_algs_from_responses(self):
        responses = [Response(
            student_uuid=uuid4(),
            exercise_uuid=uuid4(),
            is_correct=choice((True, False)),
            responded_at=datetime.now()
        ) for i in range(2)]
        response_dicts = EcosystemMatrix._response_dicts_for_algs_from_responses(responses)

        assert response_dicts == [response.dict_for_algs for response in responses]
        assert EcosystemMatrix._response_dicts_for_algs_from_responses(
            response_dicts
        ) == response_dicts

    def test_from_ecosystem_uuid_pages_responses(self):
        ecosystem_uuid = uuid4()

        page_uuids = [uuid4(), uuid4()]
        pages = [Page(uuid=uuid, exercise_uuids=[uuid4(), uuid4()]) for uuid in page_uuids]
        NC = len(page_uuids)

        exercise_uuids = [exercise_uuid for page in pages for exercise_uuid in page.exercise_uuids]
        NQ = len(exercise_uuids)

        student_uuids = [uuid4(), uuid4()]
        responses = [Response(
            student_uuid=student_uuid,
            exercise_uuid=exercise_uuid,
            is_correct=choice((True, False)),
            responded_at=datetime.now()
        ) for student_uuid in student_uuids for exercise_uuid in exercise_uuids]

        ecosystem_matrix = EcosystemMatrix.from_ecosystem_uuid_pages_responses(
            ecosystem_uuid=ecosystem_uuid, pages=pages, responses=responses
        )

        assert ecosystem_matrix.ecosystem_uuid == ecosystem_uuid
        assert set(ecosystem_matrix.Q_ids) == set(exercise_uuids)
        assert set(ecosystem_matrix.C_ids) == set(page_uuids)
        assert ecosystem_matrix.d_NQx1.shape == (NQ, 1)
        assert ecosystem_matrix.W_NCxNQ.shape == (NC, NQ)
        assert ecosystem_matrix.H_mask_NCxNQ.shape == (NC, NQ)

    def test_to_sparfa_algs_with_student_uuids_responses(self):
        ecosystem_uuid = uuid4()

        page_uuids = [uuid4(), uuid4()]
        pages = [Page(uuid=uuid, exercise_uuids=[uuid4(), uuid4()]) for uuid in page_uuids]
        NC = len(page_uuids)

        exercise_uuids = [exercise_uuid for page in pages for exercise_uuid in page.exercise_uuids]
        NQ = len(exercise_uuids)

        student_uuids = [uuid4(), uuid4()]
        responses = [Response(
            student_uuid=student_uuid,
            exercise_uuid=exercise_uuid,
            is_correct=choice((True, False)),
            responded_at=datetime.now()
        ) for student_uuid in student_uuids for exercise_uuid in exercise_uuids]

        ecosystem_matrix = EcosystemMatrix.from_ecosystem_uuid_pages_responses(
            ecosystem_uuid=ecosystem_uuid, pages=pages, responses=responses
        )

        target_student_uuids = student_uuids[:1]
        target_responses = responses[0:4]
        target_exercise_uuids = [response.exercise_uuid for response in target_responses]

        algs = ecosystem_matrix.to_sparfa_algs_with_student_uuids_responses(
            student_uuids=target_student_uuids, responses=target_responses
        )

        assert set(algs.L_ids) == set(target_student_uuids)
        assert set(algs.Q_ids) == set(target_exercise_uuids)
        assert set(algs.C_ids) == set(ecosystem_matrix.C_ids)
        assert (algs.d_NQx1 == ecosystem_matrix.d_NQx1).all()
        assert (algs.W_NCxNQ == ecosystem_matrix.W_NCxNQ).all()
        assert (algs.H_mask_NCxNQ == ecosystem_matrix.H_mask_NCxNQ).all()
