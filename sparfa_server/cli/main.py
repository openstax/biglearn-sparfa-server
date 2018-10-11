from click import group, version_option, pass_context

from ..__about__ import __version__
from . import celery, server, loaders, calcs


@group()
@version_option(version=__version__)
@pass_context
def cli(ctx):
    pass


def main():
    cli.add_command(celery)
    cli.add_command(server)
    cli.add_command(loaders)
    cli.add_command(calcs)
    cli(prog_name='sparf', obj={})
