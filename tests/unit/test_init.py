from re import match

from sparfa_server import __author__, __copyright__, __license__, __version__


def test_metadata():
    assert __author__ == 'OpenStax'
    assert match('Copyright 2017-\\d+ Rice University', __copyright__)
    assert __license__ == 'AGPLv3'
    assert match('\\d+\\.\\d+\\.\\d+', __version__)
