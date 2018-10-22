from pytest import raises
from requests.models import Response

from .vcr import BiglearnVCRTestCase
from sparfa_server.biglearn.exceptions import NotFound, raise_if_response_is_http_error, BadGateway
from sparfa_server.biglearn.clients import BiglearnClient
from sparfa_server.config import BIGLEARN_API_URL


class TestBiglearnError(BiglearnVCRTestCase):

    def test_init(self):
        with raises(NotFound) as excinfo:
            BiglearnClient(BIGLEARN_API_URL).request('get', 'fetch_ecosystem_metadatas')

        json_exception = excinfo.value
        response = json_exception.response
        assert response.status_code == 404
        assert response.json() == {'status': 404, 'error': 'Not Found'}
        assert json_exception.code == response.status_code
        assert json_exception.msg == 'Not Found'

        response._content = b'Not Found'
        non_json_exception = NotFound(response)
        assert non_json_exception.code == response.status_code == 404
        assert non_json_exception.msg == 'Not Found'

    def test_message(self):
        with raises(NotFound) as excinfo:
            BiglearnClient(BIGLEARN_API_URL).request('get', 'fetch_ecosystem_metadatas')

        assert excinfo.value.message == 'Not Found'

    def test_str(self):
        with raises(NotFound) as excinfo:
            BiglearnClient(BIGLEARN_API_URL).request('get', 'fetch_ecosystem_metadatas')

        assert str(excinfo.value) == '404 Not Found'

    def test_repr(self):
        with raises(NotFound) as excinfo:
            BiglearnClient(BIGLEARN_API_URL).request('get', 'fetch_ecosystem_metadatas')

        assert repr(excinfo.value) == '<NotFound [404 Not Found]>'


def test_raise_if_response_is_http_error():
    response = Response()

    response.status_code = 200
    assert raise_if_response_is_http_error(response) is None

    response.status_code = 502
    with raises(BadGateway):
        raise_if_response_is_http_error(response)
