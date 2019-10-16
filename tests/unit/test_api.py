def test_root_not_found(flask):
    response = flask.get('/')
    assert response.status_code == 404
    assert b'not found' in response.data
