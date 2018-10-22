from sys import exit

from click import command, option
from honcho.manager import Manager


@command()
@option(
    '--worker/--no-worker', default=True, help="Whether or not to run the celery worker process"
)
@option('--beat/--no-beat', default=True, help="Whether or not to run the celery beat process")
def server(worker, beat):
    """
    Run the Celery worker and beat processes.

    The worker defaults to using the same number of processes as the number of cores on the machine.
    """
    manager = Manager()
    if worker:
        manager.add_process('worker', 'sparfa celery worker --loglevel=info')
    if beat:
        manager.add_process('beat', 'sparfa celery beat --loglevel=info')
    manager.loop()

    exit(manager.returncode)
