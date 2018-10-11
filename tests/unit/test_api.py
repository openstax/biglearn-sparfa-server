from uuid import uuid4

from . import __version__
from .api import BiglearnClient, BiglearnApi
from unit.helper import build_url, UnitHelper


def url_for(server, endpoint):
    return build_url(server, endpoint)


class TestBiglearnApi(UnitHelper):
    """Subclass for testing ClientCore"""
    described_class = BiglearnApi

    example_data = None

    def test_create_course_event_request(self):
        request_uuid = str(uuid4())
        course_uuid = str(uuid4())
        offset = 0
        max_events = 1000

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
                    'sequence_number_offset': offset,
                }
            ],
            'max_num_events': max_events
        }

        data = create_course_event_request(course_uuid,
                                           offset,
                                           max_events,
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
            ],
            'max_num_events': 1000
        }

        data = create_ecosystem_event_request(ecosystem_uuid, 0, 1000, request_uuid)
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
        max_events = 1000
        payload = create_course_event_request(course_uuid, offset, max_events)
        url = build_url('api', 'fetch_course_events')
        self.instance.fetch_course_event_requests(payload)
        self.post_called_with(url, data=payload)

    def test_ecosystem_event_requests(self):
        ecosystem_uuid = str(uuid.uuid4())
        offset = 10
        max_events = 1000
        payload = create_ecosystem_event_request(ecosystem_uuid, offset, max_events)
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


class TestClientSession:
    def build_session(self, base_url=None):
        s = session.BiglearnSession()
        if base_url:
            s.base_url = base_url
        return s

    def test_has_default_headers(self):
        """Assert the default headers are there upon initialization"""
        s = self.build_session()

        assert 'Content-Type' in s.headers
        assert s.headers['Content-Type'] == 'application/json'
        assert 'User-Agent' in s.headers
        assert s.headers['User-Agent'] == 'Biglearn-API Python API client {0}'.format(__version__)

    def test_build_url(self):
        s = self.build_session()
        url = s.build_url('api', 'fetch_ecosystem_metadatas')
        assert url == 'https://biglearn-api-dev.openstax.org/fetch_ecosystem_metadatas'

    def test_build_url_caches_built_urls(self):
        """Test that building a URL caches it"""
        s = self.build_session()
        url = s.build_url('api', 'fetch_ecosystem_metadatas')
        url_parts = ('https://biglearn-api-dev.openstax.org', 'fetch_ecosystem_metadatas')
        assert url_parts in session.__url_cache__
        assert url in session.__url_cache__.values()

    def test_build_url_uses_a_different_base(self):
        """Test that you can pass in a different base URL to build_url"""
        s = self.build_session()
        url = s.build_url('api','fetch_matrix_calcs', base_url='https://status.openstax.org')
        assert url == 'https://status.openstax.org/fetch_matrix_calcs'

    def test_build_url_defaults_to_api(self):
        s = self.build_session()
        url = s.build_url()
        assert url == 'https://biglearn-api-dev.openstax.org'
