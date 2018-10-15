from os import environ
from sys import exit

from click import command, option
from honcho.manager import Manager


@command()
@option('--worker/--no-worker',
        default=True,
        help="Whether or not to run the celery worker process")
@option('--beat/--no-beat',
        default=True,
        help="Whether or not to run the celery beat process")
def server(worker, beat):
    """Run the celery beat process and a single celery worker (development mode)"""
    environ['PYTHONUNBUFFERED'] = 'true'

    manager = Manager()

    if worker:
        manager.add_process('worker', 'sparf celery worker --loglevel=info')

    if beat:
        manager.add_process('beat', 'sparf celery beat --loglevel=info')

    manager.loop()

    exit(manager.returncode)
