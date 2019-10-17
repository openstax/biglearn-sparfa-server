from uuid import uuid4
from datetime import datetime

from sparfa_server.config import BIGLEARN_SPARFA_TOKEN
from sparfa_server.orm import EcosystemMatrix, transaction


def test_root_not_found(flask):
    response = flask.get('/')
    assert response.status_code == 404
    assert 'not found' in response.json['errors'][0]


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
            {'ecosystem_matrix_uuid': str(uuid4()), 'student_uuids': []} for i in range(11)
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
        w_data=[],
        w_row=[],
        w_col=[],
        h_mask_data=[],
        h_mask_row=[],
        h_mask_col=[]
    )

    ecosystem_matrix_2 = EcosystemMatrix(
        uuid=str(uuid4()),
        ecosystem_uuid=str(uuid4()),
        Q_ids=[question_1_uuid, question_2_uuid],
        C_ids=[concept_1_uuid, concept_2_uuid],
        d_data=[0, 0.5],
        w_data=[1.0, 0.5],
        w_row=[0, 1],
        w_col=[0, 1],
        h_mask_data=[True, True],
        h_mask_row=[0, 1],
        h_mask_col=[0, 1],
    )

    ecosystem_matrix_3 = EcosystemMatrix(
        uuid=str(uuid4()),
        ecosystem_uuid=str(uuid4()),
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

    with transaction() as session:
        session.add(ecosystem_matrix_1)
        session.add(ecosystem_matrix_2)
        session.add(ecosystem_matrix_3)

    response = flask.post(
        '/fetch_ecosystem_matrices',
        headers={'Biglearn-Sparfa-Token': BIGLEARN_SPARFA_TOKEN},
        json={'ecosystem_matrix_requests': [
            {'ecosystem_matrix_uuid': ecosystem_matrix_1.uuid, 'student_uuids': []},
            {'ecosystem_matrix_uuid': ecosystem_matrix_2.uuid,
             'student_uuids': [student_1_uuid, student_2_uuid]},
            {'ecosystem_matrix_uuid': str(uuid4()), 'student_uuids': []}
        ]}
    )
    assert response.status_code == 200

    ecosystem_matrix_responses = response.json['ecosystem_matrices']
    assert len(ecosystem_matrix_responses) == 2

    ecosystem_matrix_by_uuid = {}
    for ecosystem_matrix in (ecosystem_matrix_1, ecosystem_matrix_2):
        ecosystem_matrix_by_uuid[ecosystem_matrix.uuid] = ecosystem_matrix

    for ecosystem_matrix_response in ecosystem_matrix_responses:
        ecosystem_matrix_uuid = ecosystem_matrix_response['ecosystem_matrix_uuid']
        ecosystem_matrix = ecosystem_matrix_by_uuid[ecosystem_matrix_uuid]

        assert ecosystem_matrix_response['ecosystem_uuid'] == ecosystem_matrix.ecosystem_uuid
        if ecosystem_matrix.superseded_at is None:
            assert ecosystem_matrix_response['superseded_at'] is None
        else:
            superseded_at_str = ecosystem_matrix.superseded_at.isoformat()
            assert ecosystem_matrix_response['superseded_at'] == superseded_at_str
        assert ecosystem_matrix_response['Q_ids'] == ecosystem_matrix.Q_ids
        assert ecosystem_matrix_response['C_ids'] == ecosystem_matrix.C_ids
        assert ecosystem_matrix_response['d_data'] == ecosystem_matrix.d_data
        assert ecosystem_matrix_response['w_data'] == ecosystem_matrix.w_data
        assert ecosystem_matrix_response['w_row'] == ecosystem_matrix.w_row
        assert ecosystem_matrix_response['w_col'] == ecosystem_matrix.w_col
        assert ecosystem_matrix_response['h_mask_data'] == ecosystem_matrix.h_mask_data
        assert ecosystem_matrix_response['h_mask_row'] == ecosystem_matrix.h_mask_row
        assert ecosystem_matrix_response['h_mask_col'] == ecosystem_matrix.h_mask_col
