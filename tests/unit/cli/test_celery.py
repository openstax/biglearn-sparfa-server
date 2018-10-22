from unittest.mock import patch

from pytest import raises

from sparfa_server.cli.celery import celery


def test_celery():
    with patch('sparfa_server.cli.celery.app', autospec=True) as app:
        with raises(SystemExit):
            celery(('control', '--help'))

    app.start.assert_called_once_with(argv=['sparfa celery', 'control', '--help'])
