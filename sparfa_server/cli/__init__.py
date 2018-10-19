from click import group, version_option

from .. import __version__
from .celery import celery
from .loaders import load
from .calcs import calc
from .server import server


@group()
@version_option(prog_name='sparfa', version=__version__)
def main():
    """CLI for biglearn-sparfa-server"""

main.add_command(celery)
main.add_command(load)
main.add_command(calc)
main.add_command(server)
