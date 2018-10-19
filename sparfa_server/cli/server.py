from sys import exit

from click import command, option, ClickException

from ..config import PY_ENV


@command()
@option('--worker/--no-worker',
        default=True,
        help="Whether or not to run the celery worker process")
@option('--beat/--no-beat',
        default=True,
        help="Whether or not to run the celery beat process")
def server(worker, beat):
    """
    Run the Celery beat process and one worker.

    For development purposes
    """
    if PY_ENV == 'production':
        exit('Error: the sparfa server command cannot be used in production mode')

    try:
        from honcho.manager import Manager
    except ImportError as exc:
        raise ClickException('{}: Please run `pip install -e .[dev]`'.format(exc.msg))

    manager = Manager()
    if worker:
        manager.add_process('worker', 'sparfa celery worker --loglevel=info')
    if beat:
        manager.add_process('beat', 'sparfa celery beat --loglevel=info')
    manager.loop()

    exit(manager.returncode)
