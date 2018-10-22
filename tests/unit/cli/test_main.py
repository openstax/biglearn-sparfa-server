from sparfa_server.cli.main import main


def test_main():
    assert set(main.commands.keys()) == set(('load', 'calc', 'server', 'celery'))
