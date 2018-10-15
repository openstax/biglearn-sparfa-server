from click import group, version_option, pass_context

from .. import __version__
from .celery import celery
from .server import server
from .loaders import loaders
from .calcs import calcs


@group()
@version_option(version=__version__)
@pass_context
def cli(ctx):
    """CLI for biglearn-sparfa-server"""


def main():
    cli.add_command(celery)
    cli.add_command(server)
    cli.add_command(loaders)
    cli.add_command(calcs)
    cli(prog_name='sparf', obj={})
