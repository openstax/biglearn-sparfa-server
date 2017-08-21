import uuid

from sparfa_server import BiglearnApi
from sparfa_server.api import create_course_event_request, \
    create_ecosystem_event_request
from unit.helper import build_url, UnitHelper


def url_for(server, endpoint):
    return build_url(server, endpoint)


class TestBiglearnApi(UnitHelper):
    """Subclass for testing ClientCore"""
    described_class = BiglearnApi

    example_data = None

    def test_create_course_event_request(self):
        request_uuid = str(uuid.uuid4())
        course_uuid = str(uuid.uuid4())
        offset = 0

        event_request = {
            'course_event_requests': [
                {
                    'request_uuid': request_uuid,
                    'event_types': [
                        'create_course',
                        'prepare_course_ecosystem',
                        'update_course_ecosystem',
                        'update_roster',
                        'update_course_active_dates',
                        'update_globally_excluded_exercises',
                        'update_course_excluded_exercises',
                        'create_update_assignment',
                        'record_response'
                    ],
                    'course_uuid': course_uuid,
                    'sequence_number_offset': offset

                }
            ]
        }

        data = create_course_event_request(course_uuid,
                                           offset,
                                           request_uuid)
        assert data == event_request

    def test_create_ecosystem_event_request(self):
        request_uuid = str(uuid.uuid4())
        ecosystem_uuid = str(uuid.uuid4())

        event_request = {
            'ecosystem_event_requests': [
                {
                    'request_uuid': request_uuid,
                    'event_types': ['create_ecosystem'],
                    'ecosystem_uuid': ecosystem_uuid,
                    'sequence_number_offset': 0,
                }
            ]
        }

        data = create_ecosystem_event_request(ecosystem_uuid, request_uuid)
        assert data == event_request

    def test_fetch_course_uuids(self):
        self.instance.fetch_course_metadatas()
        assert self.session.post.called == True

    def test_fetch_ecosystem_uuids(self):
        self.instance.fetch_ecosystem_metadatas()
        assert self.session.post.called == True

    def test_fetch_course_event_requests(self):
        course_uuid = str(uuid.uuid4())
        offset = 10
        payload = create_course_event_request(course_uuid, offset)
        url = build_url('api', 'fetch_course_events')
        self.instance.fetch_course_event_requests(payload)
        self.post_called_with(url, data=payload)

    def test_ecosystem_event_requests(self):
        ecosystem_uuid = str(uuid.uuid4())

        payload = create_ecosystem_event_request(ecosystem_uuid)
        url = build_url('api', 'fetch_ecoystem_events')
        self.instance.fetch_ecosystem_event_requests(payload)
        self.post_called_with(url, data=payload)

    def test_fetch_matrix_calculations(self):
        alg_name = 'biglearn-test'

        payload = dict(algorithm_name=alg_name)
        url = build_url('scheduler', 'fetch_ecosystem_matrix_updates')

        self.instance.fetch_matrix_calcs(payload)
        self.post_called_with(url, data=payload)

    def test_update_matrix_calculations(self):
        calc_uuid = str(uuid.uuid4())
        alg_name = 'biglearn-test'
        payload = {
            'ecosystem_matrices_updated': [
                {
                    'calculation_uuid': calc_uuid,
                    'algorithm_name': alg_name,
                },
            ],
        }
        url = build_url('scheduler', 'fetch_exercise_calculations')
        self.instance.update_matrix_calcs(payload)
        self.post_called_with(url, data=payload)
