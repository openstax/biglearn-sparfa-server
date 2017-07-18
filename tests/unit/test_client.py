import json

import io
import pytest
import requests

from sparfa_server import exceptions

from sparfa_server.client.client import ClientCore


def test_boolean(test_session):
    response = requests.Response()
    response.status_code = 200
    boolean = test_session._boolean(response=response,
                                    true_code=200,
                                    false_code=400)
    assert boolean is True


def test_boolean_raises_exception(test_session):
    response = requests.Response()
    response.status_code = 512
    response.raw = io.BytesIO()
    with pytest.raises(exceptions.ServerError):
        boolean = test_session._boolean(response=response,
                                        true_code=200,
                                        false_code=204)


def test_boolean_false_code(test_session):
    response = requests.Response()
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
    response = requests.Response()
    response.headers['Last-Modified'] = 'foo'
    response.headers['ETag'] = 'bar'
    response.raw = io.BytesIO(b'{}')
    response.status_code = 200

    json = test_session._json(response, 200)
    assert json['Last-Modified'] == 'foo'
    assert json['ETag'] == 'bar'


def test_json_status_code_does_not_match(test_session):
    """Verify JSON information is retrieved correctly."""
    response = requests.Response()
    response.status_code = 204

    json = test_session._json(response, 200)

