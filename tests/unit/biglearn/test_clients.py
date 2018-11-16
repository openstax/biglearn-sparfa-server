from requests import Session
from pytest import raises

from .vcr import BiglearnVCRTestCase
from sparfa_server.biglearn.clients import (BiglearnClient, BiglearnApi, BLAPI,
                                            BiglearnScheduler, BLSCHED)
from sparfa_server.biglearn.exceptions import NotFound
from sparfa_server.config import (BIGLEARN_API_URL, BIGLEARN_API_TOKEN,
                                  BIGLEARN_SCHED_ALGORITHM_NAME,
                                  BIGLEARN_SCHED_URL, BIGLEARN_SCHED_TOKEN)
from sparfa_server import __version__
from constants import UUID_REGEX

# To ensure consistent cassettes
REQUEST_UUID = 'c5f5c856-a11c-44e5-9493-6e1dec6daeea'
ECOSYSTEM_UUID = 'd145e892-e08f-48fe-b054-32f26c7c8bfc'
COURSE_UUID = '25d4bc9a-aec8-4337-8cad-5fcb9a0a9f90'
CALCULATION_UUID = 'b1e32df9-1915-42d9-9929-785db957d58d'
EXERCISE_UUIDS = ['29f83616-e158-461e-bdb4-3808fe353561', '4b511ecf-91d5-4967-b412-c4cd00a5140d']
CLUE_DATA = {
    'minimum': 0,
    'most_likely': 0.5,
    'maximum': 1,
    'is_real': False,
    'ecosystem_uuid': ECOSYSTEM_UUID
}


class TestBiglearnClient(BiglearnVCRTestCase):

    def test_init(self):
        client = BiglearnClient('https://www.example.com')

        assert client._base_url == 'https://www.example.com'
        session = client.session
        assert isinstance(session, Session)

        assert session.headers['Accept'] == 'application/json'
        assert session.headers['Content-Type'] == 'application/json'

    def test_request(self):
        with raises(NotFound):
            BiglearnClient(BIGLEARN_API_URL).request('get', 'fetch_ecosystem_metadatas')

    def test_post(self):
        client = BiglearnClient(BIGLEARN_API_URL)
        client.session.headers.update({
            'Biglearn-Api-Token': BIGLEARN_API_TOKEN,
            'User-Agent': 'Biglearn-Scheduler Python API client {}'.format(__version__)
        })
        response = client.post('fetch_ecosystem_events', json={
            'ecosystem_event_requests': [
                {
                    'request_uuid': REQUEST_UUID,
                    'event_types': ['create_ecosystem'],
                    'ecosystem_uuid': ECOSYSTEM_UUID,
                    'sequence_number_offset': 0
                }
            ],
            'max_num_events': 1000
        })
        assert response == {
            'ecosystem_event_responses': [
                {
                    'request_uuid': REQUEST_UUID,
                    'ecosystem_uuid': ECOSYSTEM_UUID,
                    'events': [], 'is_gap': False, 'is_end': True
                }
            ]
        }


class TestBiglearnApi(BiglearnVCRTestCase):

    def test_init(self):
        client = BiglearnApi('Some Token')
        assert client._base_url == BIGLEARN_API_URL

        session = client.session
        assert session.headers['Biglearn-Api-Token'] == 'Some Token'
        assert session.headers['User-Agent'] == \
            'Biglearn-API Python API client {}'.format(__version__)

    def test_fetch_ecosystem_metadatas(self):
        responses = BLAPI.fetch_ecosystem_metadatas(
            metadata_sequence_number_offset=42, max_num_metadatas=10
        )
        for response in responses:
            assert set(response.keys()) == set(('uuid', 'metadata_sequence_number'))
            assert UUID_REGEX.match(response['uuid'])
            assert isinstance(response['metadata_sequence_number'], int)

    def test_fetch_ecosystem_events(self):
        responses = BLAPI.fetch_ecosystem_events([{
            'ecosystem_uuid': ECOSYSTEM_UUID,
            'sequence_number_offset': 0,
            'event_types': ['create_ecosystem'],
            'request_uuid': REQUEST_UUID
        }])
        assert responses == [
            {
                'request_uuid': REQUEST_UUID,
                'ecosystem_uuid': ECOSYSTEM_UUID,
                'events': [], 'is_gap': False, 'is_end': True
            }
        ]

    def test_fetch_course_metadatas(self):
        responses = BLAPI.fetch_course_metadatas(
            metadata_sequence_number_offset=42, max_num_metadatas=10
        )
        for response in responses:
            assert set(response.keys()) == set(
                ('uuid', 'metadata_sequence_number', 'initial_ecosystem_uuid')
            )
            assert UUID_REGEX.match(response['uuid'])
            assert isinstance(response['metadata_sequence_number'], int)
            assert UUID_REGEX.match(response['initial_ecosystem_uuid'])

    def test_fetch_course_events(self):
        responses = BLAPI.fetch_course_events([{
            'course_uuid': COURSE_UUID,
            'sequence_number_offset': 0,
            'event_types': ['create_course'],
            'request_uuid': REQUEST_UUID
        }])
        assert responses == [
            {
                'request_uuid': REQUEST_UUID,
                'course_uuid': COURSE_UUID,
                'events': [], 'is_gap': False, 'is_end': True
            }
        ]


class TestBiglearnScheduler(BiglearnVCRTestCase):

    def test_init(self):
        client = BiglearnScheduler('Some Token')
        assert client._base_url == BIGLEARN_SCHED_URL

        session = client.session
        assert session.headers['Biglearn-Scheduler-Token'] == 'Some Token'
        assert session.headers['User-Agent'] == \
            'Biglearn-Scheduler Python API client {}'.format(__version__)

    def test_update_with_algorithm_names(self):
        requests = [{}, {'test': True}]
        BLSCHED._update_with_algorithm_name(requests)
        assert requests == [
            {'algorithm_name': BIGLEARN_SCHED_ALGORITHM_NAME},
            {'test': True, 'algorithm_name': BIGLEARN_SCHED_ALGORITHM_NAME}
        ]

    def test_fetch_ecosystem_matrix_updates(self):
        responses = BLSCHED.fetch_ecosystem_matrix_updates()
        for response in responses:
            assert set(response.keys()) == set(('ecosystem_uuid', 'calculation_uuid'))
            assert UUID_REGEX.match(response['ecosystem_uuid'])
            assert UUID_REGEX.match(response['calculation_uuid'])

    def test_ecosystem_matrices_updated(self):
        responses = BLSCHED.ecosystem_matrices_updated([{'calculation_uuid': CALCULATION_UUID}])
        assert len(responses) == 1
        response = responses[0]
        assert set(response.keys()) == set(('calculation_uuid', 'calculation_status'))
        assert response['calculation_uuid'] == CALCULATION_UUID
        assert response['calculation_status'] == 'calculation_unknown'

    def test_fetch_exercise_calculations(self):
        responses = BLSCHED.fetch_exercise_calculations()
        for response in responses:
            assert set(response.keys()) == set((
                'calculation_uuid', 'ecosystem_uuid', 'exercise_uuids', 'student_uuid'
            ))
            assert UUID_REGEX.match(response['calculation_uuid'])
            assert UUID_REGEX.match(response['ecosystem_uuid'])
            for exercise_uuid in response['exercise_uuids']:
                assert UUID_REGEX.match(exercise_uuid)
            assert UUID_REGEX.match(response['student_uuid'])

    def test_update_exercise_calculations(self):
        responses = BLSCHED.update_exercise_calculations([{
            'calculation_uuid': CALCULATION_UUID, 'exercise_uuids': EXERCISE_UUIDS
        }])
        assert len(responses) == 1
        response = responses[0]
        assert set(response.keys()) == set(('calculation_uuid', 'calculation_status'))
        assert response['calculation_uuid'] == CALCULATION_UUID
        assert response['calculation_status'] == 'calculation_unknown'

    def test_fetch_clue_calculations(self):
        responses = BLSCHED.fetch_clue_calculations()
        for response in responses:
            assert set(response.keys()) == set((
                'ecosystem_uuid', 'responses', 'calculation_uuid', 'student_uuids', 'exercise_uuids'
            ))
            assert UUID_REGEX.match(response['ecosystem_uuid'])
            for rr in response['responses']:
                assert set(rr.keys()) == set(('response_uuid', 'trial_uuid', 'is_correct'))
                assert UUID_REGEX.match(rr['response_uuid'])
                assert UUID_REGEX.match(rr['trial_uuid'])
                assert type(rr['is_correct']) == bool
            assert UUID_REGEX.match(response['calculation_uuid'])
            for student_uuid in response['student_uuids']:
                assert UUID_REGEX.match(student_uuid)
            for exercise_uuid in response['exercise_uuids']:
                assert UUID_REGEX.match(exercise_uuid)

    def test_update_clue_calculations(self):
        responses = BLSCHED.update_clue_calculations([{
            'calculation_uuid': CALCULATION_UUID, 'clue_data': CLUE_DATA
        }])
        assert len(responses) == 1
        response = responses[0]
        assert set(response.keys()) == set(('calculation_uuid', 'calculation_status'))
        assert response['calculation_uuid'] == CALCULATION_UUID
        assert response['calculation_status'] == 'calculation_unknown'
