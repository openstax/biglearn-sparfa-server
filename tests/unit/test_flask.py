def test_root(flask):
    response = flask.get('/')
    assert response.status_code == 200
    assert response.get_data(as_text=True) == 'Biglearn SPARFA'


def test_ping(flask):
    response = flask.get('/ping')
    assert response.status_code == 200
    assert not response.get_data()
