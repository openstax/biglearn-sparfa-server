from unittest.mock import patch

from pytest import raises

from sparfa_server.cli.server import server


def test_server():
    with patch('sparfa_server.cli.server.Manager', autospec=True) as Manager:
        with patch('sparfa_server.cli.server.exit', autospec=True) as exit:
            with raises(SystemExit):
                server(())

    manager = Manager()
    assert manager.add_process.call_count == 2
    manager.add_process.assert_any_call('worker', 'sparfa celery worker --loglevel=info')
    manager.add_process.assert_called_with('beat', 'sparfa celery beat --loglevel=info')
    manager.loop.assert_called_once()
    exit.assert_called_once_with(manager.returncode)
