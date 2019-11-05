from uuid import uuid4
from datetime import datetime, timedelta
from random import choice

from sparfa_server.config import BIGLEARN_SPARFA_TOKEN
from sparfa_server.orm import EcosystemMatrix, Response, transaction


def test_fetch_ecosystem_matrices_get_not_allowed(flask):
    response = flask.get('/fetch_ecosystem_matrices')
    assert response.status_code == 405
    assert 'method is not allowed' in response.json['errors'][0]


def test_fetch_ecosystem_matrices_no_token(flask):
    response = flask.post('/fetch_ecosystem_matrices')
    assert response.status_code == 401
    assert 'missing the Biglearn-Sparfa-Token' in response.json['errors'][0]


def test_fetch_ecosystem_matrices_invalid_token(flask):
    response = flask.post('/fetch_ecosystem_matrices',
                          headers={'Biglearn-Sparfa-Token': 'Invalid'})
    assert response.status_code == 401
    assert 'Invalid Biglearn-Sparfa-Token' in response.json['errors'][0]


def test_fetch_ecosystem_matrices_no_body(flask):
    response = flask.post('/fetch_ecosystem_matrices',
                          headers={'Biglearn-Sparfa-Token': BIGLEARN_SPARFA_TOKEN})
    assert response.status_code == 400
    assert 'sent a request that this server could not understand' in response.json['errors'][0]


def test_fetch_ecosystem_matrices_no_ecosystem_matrix_requests_key(flask):
    response = flask.post('/fetch_ecosystem_matrices',
                          headers={'Biglearn-Sparfa-Token': BIGLEARN_SPARFA_TOKEN},
                          json={})
    assert response.status_code == 400
    assert "must contain ['ecosystem_matrix_requests']" in response.json['errors'][0]


def test_fetch_ecosystem_matrices_too_many_ecosystem_matrix_requests(flask):
    response = flask.post(
        '/fetch_ecosystem_matrices',
        headers={'Biglearn-Sparfa-Token': BIGLEARN_SPARFA_TOKEN},
        json={'ecosystem_matrix_requests': [
            {'request_uuid': str(uuid4()), 'ecosystem_matrix_uuid': str(uuid4())} for i in range(11)
        ]}
    )
    assert response.status_code == 400
    assert 'ecosystem_matrix_requests must contain less than or equal to 10 items' \
        in response.json['errors'][0]


def test_fetch_ecosystem_matrices_no_ecosystem_matrix_requests(flask):
    response = flask.post('/fetch_ecosystem_matrices',
                          headers={'Biglearn-Sparfa-Token': BIGLEARN_SPARFA_TOKEN},
                          json={'ecosystem_matrix_requests': []})
    assert response.status_code == 200
    assert not response.json['ecosystem_matrices']


def test_fetch_ecosystem_matrices(flask):
    question_1_uuid = str(uuid4())
    question_2_uuid = str(uuid4())
    concept_1_uuid = str(uuid4())
    concept_2_uuid = str(uuid4())
    student_1_uuid = str(uuid4())
    student_2_uuid = str(uuid4())

    ecosystem_matrix_1 = EcosystemMatrix(
        uuid=str(uuid4()),
        ecosystem_uuid=str(uuid4()),
        superseded_at=datetime.now(),
        Q_ids=[],
        C_ids=[],
        d_data=[],
        W_data=[],
        W_row=[],
        W_col=[],
        H_mask_data=[],
        H_mask_row=[],
        H_mask_col=[]
    )

    ecosystem_matrix_2 = EcosystemMatrix(
        uuid=str(uuid4()),
        ecosystem_uuid=str(uuid4()),
        Q_ids=[question_1_uuid, question_2_uuid],
        C_ids=[concept_1_uuid, concept_2_uuid],
        d_data=[0, 0.5],
        W_data=[1.0, 0.5],
        W_row=[0, 1],
        W_col=[0, 1],
        H_mask_data=[True, True],
        H_mask_row=[0, 1],
        H_mask_col=[0, 1]
    )

    ecosystem_matrix_3 = EcosystemMatrix(
        uuid=str(uuid4()),
        ecosystem_uuid=str(uuid4()),
        Q_ids=[],
        C_ids=[],
        d_data=[],
        W_data=[],
        W_row=[],
        W_col=[],
        H_mask_data=[],
        H_mask_row=[],
        H_mask_col=[]
    )

    responded_before = datetime.utcnow()

    response_1 = Response(
        uuid=str(uuid4()),
        course_uuid=str(uuid4()),
        ecosystem_uuid=ecosystem_matrix_2.ecosystem_uuid,
        trial_uuid=str(uuid4()),
        student_uuid=str(uuid4()),
        exercise_uuid=str(uuid4()),
        is_correct=choice((True, False)),
        is_real_response=choice((True, False)),
        responded_at=responded_before - timedelta(days=1)
    )

    response_2 = Response(
        uuid=str(uuid4()),
        course_uuid=str(uuid4()),
        ecosystem_uuid=ecosystem_matrix_2.ecosystem_uuid,
        trial_uuid=str(uuid4()),
        student_uuid=str(uuid4()),
        exercise_uuid=str(uuid4()),
        is_correct=choice((True, False)),
        is_real_response=choice((True, False)),
        responded_at=responded_before + timedelta(days=1)
    )

    with transaction() as session:
        session.add(ecosystem_matrix_1)
        session.add(ecosystem_matrix_2)
        session.add(ecosystem_matrix_3)
        session.add(response_1)
        session.add(response_2)

    requests = [
        {
            'request_uuid': str(uuid4()),
            'ecosystem_matrix_uuid': ecosystem_matrix_1.uuid,
            'student_uuids': []
        },
        {
            'request_uuid': str(uuid4()),
            'ecosystem_matrix_uuid': ecosystem_matrix_2.uuid,
            'student_uuids': [student_1_uuid, student_2_uuid],
            'responded_before': responded_before.isoformat() + 'Z'
        },
        {
            'request_uuid': str(uuid4()),
            'ecosystem_matrix_uuid': ecosystem_matrix_2.uuid
        },
        {
            'request_uuid': str(uuid4()),
            'ecosystem_matrix_uuid': str(uuid4())
        }
    ]
    requests_by_uuid = {request['request_uuid']: request for request in requests}

    response = flask.post(
        '/fetch_ecosystem_matrices',
        headers={'Biglearn-Sparfa-Token': BIGLEARN_SPARFA_TOKEN},
        json={'ecosystem_matrix_requests': requests}
    )
    assert response.status_code == 200

    ecosystem_matrix_responses = response.json['ecosystem_matrices']
    assert len(ecosystem_matrix_responses) == 4

    ecosystem_matrix_by_uuid = {}
    for ecosystem_matrix in (ecosystem_matrix_1, ecosystem_matrix_2):
        ecosystem_matrix_by_uuid[ecosystem_matrix.uuid] = ecosystem_matrix

    for ecosystem_matrix_response in ecosystem_matrix_responses:
        request = requests_by_uuid[ecosystem_matrix_response['request_uuid']]

        ecosystem_matrix_uuid = ecosystem_matrix_response['ecosystem_matrix_uuid']
        assert ecosystem_matrix_uuid == request['ecosystem_matrix_uuid']

        ecosystem_matrix = ecosystem_matrix_by_uuid.get(ecosystem_matrix_uuid)

        if request.get('student_uuids') is not None:
            assert ecosystem_matrix_response['L_ids'] == request['student_uuids']
        elif ecosystem_matrix:
            assert isinstance(ecosystem_matrix_response['L_ids'], list)
        else:
            assert ecosystem_matrix_response['L_ids'] == []

        if ecosystem_matrix:
            assert ecosystem_matrix_response['ecosystem_uuid'] == ecosystem_matrix.ecosystem_uuid
            assert ecosystem_matrix_response['Q_ids'] == ecosystem_matrix.Q_ids
            assert ecosystem_matrix_response['C_ids'] == ecosystem_matrix.C_ids
            assert ecosystem_matrix_response['d_data'] == ecosystem_matrix.d_data
            assert ecosystem_matrix_response['W_data'] == ecosystem_matrix.W_data
            assert ecosystem_matrix_response['W_row'] == ecosystem_matrix.W_row
            assert ecosystem_matrix_response['W_col'] == ecosystem_matrix.W_col
            assert ecosystem_matrix_response['H_mask_data'] == ecosystem_matrix.H_mask_data
            assert ecosystem_matrix_response['H_mask_row'] == ecosystem_matrix.H_mask_row
            assert ecosystem_matrix_response['H_mask_col'] == ecosystem_matrix.H_mask_col
            assert isinstance(ecosystem_matrix_response['G_data'], list)
            assert isinstance(ecosystem_matrix_response['G_row'], list)
            assert isinstance(ecosystem_matrix_response['G_col'], list)
            assert isinstance(ecosystem_matrix_response['G_mask_data'], list)
            assert isinstance(ecosystem_matrix_response['G_mask_row'], list)
            assert isinstance(ecosystem_matrix_response['G_mask_col'], list)
            assert isinstance(ecosystem_matrix_response['U_data'], list)
            assert isinstance(ecosystem_matrix_response['U_row'], list)
            assert isinstance(ecosystem_matrix_response['U_col'], list)
            if ecosystem_matrix.superseded_at is None:
                assert ecosystem_matrix_response['superseded_at'] is None
            else:
                superseded_at_str = ecosystem_matrix.superseded_at.isoformat() + 'Z'
                assert ecosystem_matrix_response['superseded_at'] == superseded_at_str
        else:
            assert ecosystem_matrix_response['ecosystem_uuid'] is None
            assert ecosystem_matrix_response['Q_ids'] == []
            assert ecosystem_matrix_response['C_ids'] == []
            assert ecosystem_matrix_response['d_data'] == []
            assert ecosystem_matrix_response['W_data'] == []
            assert ecosystem_matrix_response['W_row'] == []
            assert ecosystem_matrix_response['W_col'] == []
            assert ecosystem_matrix_response['H_mask_data'] == []
            assert ecosystem_matrix_response['H_mask_row'] == []
            assert ecosystem_matrix_response['H_mask_col'] == []
            assert ecosystem_matrix_response['G_data'] == []
            assert ecosystem_matrix_response['G_row'] == []
            assert ecosystem_matrix_response['G_col'] == []
            assert ecosystem_matrix_response['G_mask_data'] == []
            assert ecosystem_matrix_response['G_mask_row'] == []
            assert ecosystem_matrix_response['G_mask_col'] == []
            assert ecosystem_matrix_response['U_data'] == []
            assert ecosystem_matrix_response['U_row'] == []
            assert ecosystem_matrix_response['U_col'] == []
            assert ecosystem_matrix_response['superseded_at'] is None
