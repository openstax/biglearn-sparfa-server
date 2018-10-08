import click

from sparfa_server.__about__ import __version__
from sparfa_server.cli.commands.loaders import loaders
from sparfa_server.cli.commands.calcs import calcs
from sparfa_server.cli.commands.celery import celery
from sparfa_server.cli.commands.server import server


@click.group()
@click.version_option(version=__version__)
@click.pass_context
def cli(ctx):
    pass


def main():
    cli.add_command(calcs)
    cli.add_command(loaders)
    cli.add_command(celery)
    cli.add_command(server)
    cli(prog_name='sparf', obj={})
