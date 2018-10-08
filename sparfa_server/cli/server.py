from os import environ
from sys import exit

from click import group, option


@group()
def server():
    """Manage Server commands"""


@server.command()
@option('--worker/--no-worker',
        default=True,
        help="Whether or not to run the celery worker process")
@option('--beat/--no-beat',
        default=True,
        help="Whether or not to run the celery beat process")
def server(worker, beat):
    """
    Run the development worker and scheduler
    """
    try:
        from honcho.manager import Manager
    except ImportError:
        raise click.ClickException(
            'cannot import honcho: did you run `pip install -e .` yet?')

    environ['PYTHONUNBUFFERED'] = 'true'

    m = Manager()

    if worker:
        m.add_process('worker', 'sparf celery worker --loglevel=info')

    if beat:
        m.add_process('beat', 'sparf celery beat --loglevel=info')

    m.loop()

    exit(m.returncode)
