from sparfa_server import BiglearnApi
from sparfa_server.api import create_course_event_request
from unit.helper import build_url, UnitHelper


def url_for(server, endpoint):
    return build_url(server, endpoint)


class TestBiglearnApi(UnitHelper):
    """Subclass for testing ClientCore"""
    described_class = BiglearnApi

    example_data = None

    def test_fetch_course_uuids(self):
        self.instance.fetch_course_metadatas()
        assert self.session.post.called == True

    def test_fetch_ecosystem_uuids(self):
        self.instance.fetch_ecosystem_metadatas()
        assert self.session.post.called == True

    def test_fetch_course_event_requests(self):
        course_uuid = 'fe93849300292029kldfj930489384'
        offset = 10
        max_events = 100
        payload = create_course_event_request(course_uuid, offset, max_events)
        url = build_url('api', 'fetch_course_events')
        self.instance.fetch_course_event_requests(payload)
        self.post_called_with(url, data=payload)
