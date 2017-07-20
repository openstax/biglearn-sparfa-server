import click

from sparfa_server.__about__ import __client_version__
from sparfa_server.cli.commands.loaders import loaders

SUBCOMMANDS = (
    'sparfa_server.cli.commands.loaders.loaders'
)


@click.group()
@click.version_option(version=__client_version__)
@click.pass_context
def cli(ctx):
    pass


def main():
    cli.add_command(loaders)
    cli(prog_name='sparf', obj={})

