import os

import click
import sys


@click.group()
def server():
    """Manage Server commands"""


@server.command()
@click.option('--worker/--no-worker',
              default=True,
              help="Whether or not to run the celery worker process")
@click.option('--beat/--no-beat',
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

    os.environ['PYTHONUNBUFFERED'] = 'true'

    m = Manager()

    if worker:
        m.add_process('worker', 'sparf celery worker --loglevel=info')

    if beat:
        m.add_process('beat', 'sparf celery beat --loglevel=info')

    m.loop()

    sys.exit(m.returncode)
