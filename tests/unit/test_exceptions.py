from io import BytesIO
from pytest import raises
from requests import Response

from . import exceptions

from .api import BiglearnClient


def test_boolean(test_session):
    response = Response()
    response.status_code = 200
    boolean = test_session._boolean(response=response,
                                    true_code=200,
                                    false_code=400)
    assert boolean is True


def test_boolean_raises_exception(test_session):
    response = Response()
    response.status_code = 512
    response.raw = BytesIO()
    with raises(exceptions.ServerError):
        boolean = test_session._boolean(response=response,
                                        true_code=200,
                                        false_code=204)


def test_boolean_false_code(test_session):
    response = Response()
    response.status_code = 204
    boolean = test_session._boolean(response=response,
                                    true_code=200,
                                    false_code=204)
    assert boolean is False


def test_boolean_empty_response(test_session):
    boolean = test_session._boolean(response=None,
                                    true_code=200,
                                    false_code=204)
    assert boolean is False


def test_from_json(test_session):
    core = ClientCore('{}')
    assert isinstance(core, ClientCore)


def test_json(test_session):
    response = Response()
    response.headers['Last-Modified'] = 'foo'
    response.headers['ETag'] = 'bar'
    response.raw = BytesIO(b'{}')
    response.status_code = 200

    json = test_session._json(response, 200)
    assert json['Last-Modified'] == 'foo'
    assert json['ETag'] == 'bar'


def test_json_status_code_does_not_match(test_session):
    """Verify JSON information is retrieved correctly."""
    response = Response()
    response.status_code = 204

    json = test_session._json(response, 200)
