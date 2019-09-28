from uuid import uuid4, UUID
from random import choice, shuffle
from datetime import datetime
from unittest.mock import patch
from contextlib import closing

from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql.expression import func

from sparfa_server.orm.sessions import ENGINE
from sparfa_server.orm import Ecosystem, Page, Response, EcosystemMatrix
from sparfa_server.tasks.calcs import (calculate_ecosystem_matrices,
                                       calculate_exercises,
                                       calculate_clues)


def test_calculate_ecosystem_matrices(transaction):
    ecosystem_1 = Ecosystem(
      uuid=str(uuid4()),
      metadata_sequence_number=0,
      sequence_number=1,
      last_ecosystem_matrix_update_calculation_uuid=str(uuid4())
    )

    calculation_uuid = str(uuid4())
    ecosystem_matrix_updates = [{
        'calculation_uuid': calculation_uuid, 'ecosystem_uuid': ecosystem_1.uuid
    }]

    with patch(
        'sparfa_server.tasks.calcs.BLSCHED.fetch_ecosystem_matrix_updates', autospec=True
    ) as fetch_ecosystem_matrix_updates:
        fetch_ecosystem_matrix_updates.return_value = ecosystem_matrix_updates

        with patch(
            'sparfa_server.tasks.calcs.BLSCHED.ecosystem_matrices_updated', autospec=True
        ) as ecosystem_matrices_updated:
            calculate_ecosystem_matrices()

    ecosystem_matrices_updated.assert_not_called()

    with transaction() as session:
        assert not session.query(EcosystemMatrix).all()

    ecosystem_2 = Ecosystem(uuid=str(uuid4()), metadata_sequence_number=1, sequence_number=0)

    page_1 = Page(uuid=str(uuid4()), ecosystem_uuid=ecosystem_1.uuid,
                  exercise_uuids=[str(uuid4()), str(uuid4())])
    page_2 = Page(uuid=str(uuid4()), ecosystem_uuid=ecosystem_1.uuid,
                  exercise_uuids=[str(uuid4()), str(uuid4())])
    pages = [page_1, page_2]
    exercise_uuids = [exercise_uuid for page in pages for exercise_uuid in page.exercise_uuids]

    response_1 = Response(
        uuid=str(uuid4()),
        course_uuid=str(uuid4()),
        ecosystem_uuid=ecosystem_1.uuid,
        trial_uuid=str(uuid4()),
        student_uuid=str(uuid4()),
        exercise_uuid=page_1.exercise_uuids[0],
        is_correct=choice((True, False)),
        is_real_response=choice((True, False)),
        responded_at=datetime.now()
    )
    response_2 = Response(
        uuid=str(uuid4()),
        course_uuid=str(uuid4()),
        ecosystem_uuid=ecosystem_1.uuid,
        trial_uuid=str(uuid4()),
        student_uuid=str(uuid4()),
        exercise_uuid=page_2.exercise_uuids[1],
        is_correct=choice((True, False)),
        is_real_response=choice((True, False)),
        responded_at=datetime.now()
    )

    with transaction() as session:
        session.add(ecosystem_1)
        session.add(ecosystem_2)

        session.add(page_1)
        session.add(page_2)

        session.add(response_1)
        session.add(response_2)

        assert not session.query(EcosystemMatrix).all()

    with patch(
        'sparfa_server.tasks.calcs.BLSCHED.fetch_ecosystem_matrix_updates', autospec=True
    ) as fetch_ecosystem_matrix_updates:
        fetch_ecosystem_matrix_updates.side_effect = [ecosystem_matrix_updates, []]

        with patch(
            'sparfa_server.tasks.calcs.BLSCHED.ecosystem_matrices_updated', autospec=True
        ) as ecosystem_matrices_updated:
            calculate_ecosystem_matrices()

    assert fetch_ecosystem_matrix_updates.call_count == 2
    ecosystem_matrices_updated.assert_called_once_with([{'calculation_uuid': calculation_uuid}])

    with transaction() as session:
        ecosystem_matrices = session.query(EcosystemMatrix).all()

    assert len(ecosystem_matrices) == 1
    ecosystem_matrix = ecosystem_matrices[0]
    assert ecosystem_matrix.uuid == ecosystem_1.uuid
    assert set(ecosystem_matrix.C_ids) == set(page.uuid for page in pages)
    assert set(ecosystem_matrix.Q_ids) == set(exercise_uuids)
    assert ecosystem_matrix.d_NQx1.shape == (ecosystem_matrix.NQ, 1)
    assert ecosystem_matrix.W_NCxNQ.shape == (ecosystem_matrix.NC, ecosystem_matrix.NQ)
    assert ecosystem_matrix.H_mask_NCxNQ.shape == (ecosystem_matrix.NC, ecosystem_matrix.NQ)


def test_calculate_exercises(transaction):
    ecosystem = Ecosystem(uuid=str(uuid4()), metadata_sequence_number=0, sequence_number=1)

    page_1 = Page(uuid=str(uuid4()), ecosystem_uuid=ecosystem.uuid,
                  exercise_uuids=[str(uuid4()), str(uuid4())])
    page_2 = Page(uuid=str(uuid4()), ecosystem_uuid=ecosystem.uuid,
                  exercise_uuids=[str(uuid4()), str(uuid4())])
    pages = [page_1, page_2]
    unknown_exercise_uuid = str(uuid4())
    exercise_uuids = [unknown_exercise_uuid] + [
        exercise_uuid for page in pages for exercise_uuid in page.exercise_uuids
    ]
    shuffle(exercise_uuids)

    student_uuid = str(uuid4())

    response_1 = Response(
        uuid=str(uuid4()),
        course_uuid=str(uuid4()),
        ecosystem_uuid=ecosystem.uuid,
        trial_uuid=str(uuid4()),
        student_uuid=student_uuid,
        exercise_uuid=page_1.exercise_uuids[0],
        is_correct=choice((True, False)),
        is_real_response=choice((True, False)),
        responded_at=datetime.now()
    )
    response_2 = Response(
        uuid=str(uuid4()),
        course_uuid=str(uuid4()),
        ecosystem_uuid=ecosystem.uuid,
        trial_uuid=str(uuid4()),
        student_uuid=student_uuid,
        exercise_uuid=page_2.exercise_uuids[1],
        is_correct=choice((True, False)),
        is_real_response=choice((True, False)),
        responded_at=datetime.now()
    )
    responses = [response_1, response_2]

    calculation_uuid = str(uuid4())
    exercise_calculations = [{
        'calculation_uuid': calculation_uuid,
        'ecosystem_uuid': ecosystem.uuid,
        'student_uuid': student_uuid,
        'exercise_uuids': exercise_uuids
    }]

    with patch(
        'sparfa_server.tasks.calcs.BLSCHED.fetch_exercise_calculations', autospec=True
    ) as fetch_exercise_calculations:
        fetch_exercise_calculations.return_value = exercise_calculations

        with patch(
            'sparfa_server.tasks.calcs.BLSCHED.update_exercise_calculations', autospec=True
        ) as update_exercise_calculations:
            with closing(sessionmaker(bind=ENGINE)()) as session:
                query = [func.pg_try_advisory_xact_lock(
                    (UUID(calculation['calculation_uuid']).int >> 64) - 2**63
                ) for calculation in exercise_calculations]
                session.query(*query).one()
                calculate_exercises()

            calculate_exercises()

    update_exercise_calculations.assert_not_called()

    ecosystem_matrix = EcosystemMatrix.from_ecosystem_uuid_pages_responses(
        ecosystem_uuid=ecosystem.uuid, pages=pages, responses=responses
    )

    with transaction() as session:
        session.add(ecosystem)

        session.add(page_1)
        session.add(page_2)

        session.add(response_1)
        session.add(response_2)

        session.add(ecosystem_matrix)

    with patch(
        'sparfa_server.tasks.calcs.BLSCHED.fetch_exercise_calculations', autospec=True
    ) as fetch_exercise_calculations:
        fetch_exercise_calculations.side_effect = [exercise_calculations, []]

        with patch(
            'sparfa_server.tasks.calcs.BLSCHED.update_exercise_calculations', autospec=True
        ) as update_exercise_calculations:
            calculate_exercises()

    update_exercise_calculations.assert_called_once()
    args = update_exercise_calculations.call_args
    assert len(args) == 2
    assert not args[1]
    assert len(args[0]) == 1
    exercise_calculations = args[0][0]
    assert len(exercise_calculations) == 1
    exercise_calculation = exercise_calculations[0]
    assert exercise_calculation['calculation_uuid'] == calculation_uuid
    assert set(exercise_calculation['exercise_uuids']) == set(exercise_uuids)
    assert exercise_calculation['exercise_uuids'][-1] == unknown_exercise_uuid


def test_calculate_clues(transaction):
    course_uuid = str(uuid4())
    ecosystem = Ecosystem(uuid=str(uuid4()), metadata_sequence_number=0, sequence_number=1)

    page_1 = Page(uuid=str(uuid4()), ecosystem_uuid=ecosystem.uuid,
                  exercise_uuids=[str(uuid4()), str(uuid4())])
    page_2 = Page(uuid=str(uuid4()), ecosystem_uuid=ecosystem.uuid,
                  exercise_uuids=[str(uuid4()), str(uuid4())])
    pages = [page_1, page_2]
    unknown_exercise_uuid = str(uuid4())
    exercise_uuids = [unknown_exercise_uuid] + [
        exercise_uuid for page in pages for exercise_uuid in page.exercise_uuids
    ]
    shuffle(exercise_uuids)

    student_1_uuid = str(uuid4())
    student_2_uuid = str(uuid4())
    student_uuids = [student_1_uuid, student_2_uuid]

    responses = [Response(
        uuid=str(uuid4()),
        course_uuid=course_uuid,
        ecosystem_uuid=ecosystem.uuid,
        trial_uuid=str(uuid4()),
        student_uuid=student_uuid,
        exercise_uuid=exercise_uuid,
        is_correct=choice((True, False)),
        is_real_response=choice((True, False)),
        responded_at=datetime.now()
    ) for student_uuid in student_uuids for exercise_uuid in exercise_uuids]
    shuffle(responses)
    response_dicts = [{
        'response_uuid': response.uuid,
        'trial_uuid': response.trial_uuid,
        'is_correct': response.is_correct
    } for response in responses]

    calculation_uuid = str(uuid4())
    clue_calculations = [{
        'calculation_uuid': calculation_uuid,
        'ecosystem_uuid': ecosystem.uuid,
        'student_uuids': student_uuids,
        'exercise_uuids': exercise_uuids,
        'responses': response_dicts
    }]

    with patch(
        'sparfa_server.tasks.calcs.BLSCHED.fetch_clue_calculations', autospec=True
    ) as fetch_clue_calculations:
        fetch_clue_calculations.return_value = clue_calculations

        with patch(
            'sparfa_server.tasks.calcs.BLSCHED.update_clue_calculations', autospec=True
        ) as update_clue_calculations:
            calculate_clues()

    update_clue_calculations.assert_not_called()

    ecosystem_matrix = EcosystemMatrix.from_ecosystem_uuid_pages_responses(
        ecosystem_uuid=ecosystem.uuid, pages=pages, responses=responses
    )

    with transaction() as session:
        session.add(ecosystem)

        session.add(page_1)
        session.add(page_2)

        session.add(ecosystem_matrix)

    with patch(
        'sparfa_server.tasks.calcs.BLSCHED.fetch_clue_calculations', autospec=True
    ) as fetch_clue_calculations:
        fetch_clue_calculations.return_value = clue_calculations

        with patch(
            'sparfa_server.tasks.calcs.BLSCHED.update_clue_calculations', autospec=True
        ) as update_clue_calculations:
            calculate_clues()

    update_clue_calculations.assert_not_called()

    with transaction() as session:
        session.upsert_models(Response, responses)

    with patch(
        'sparfa_server.tasks.calcs.BLSCHED.fetch_clue_calculations', autospec=True
    ) as fetch_clue_calculations:
        fetch_clue_calculations.side_effect = [clue_calculations, []]

        with patch(
            'sparfa_server.tasks.calcs.BLSCHED.update_clue_calculations', autospec=True
        ) as update_clue_calculations:
            calculate_clues()

    update_clue_calculations.assert_called_once()
    args = update_clue_calculations.call_args
    assert len(args) == 2
    assert not args[1]
    assert len(args[0]) == 1
    clue_calculations = args[0][0]
    assert len(clue_calculations) == 1
    clue_calculation = clue_calculations[0]
    assert clue_calculation['calculation_uuid'] == calculation_uuid
    clue_data = clue_calculation['clue_data']
    assert isinstance(clue_data['minimum'], float)
    assert isinstance(clue_data['most_likely'], float)
    assert isinstance(clue_data['maximum'], float)
    assert clue_data['minimum'] <= clue_data['most_likely'] <= clue_data['maximum']
    assert clue_data['is_real']
    assert clue_data['ecosystem_uuid'] == ecosystem.uuid
