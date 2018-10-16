from logging import getLogger

from click import group, pass_context

from ..tasks.calcs import (calculate_ecosystem_matrices,
                           calculate_exercises,
                           calculate_clues)


@group()
def calc():
    """Run Calculations."""


@calc.command()
def ecosystem_matrices():
    """Calculate all ecosystem matrices"""
    calculate_ecosystem_matrices()


@calc.command()
def exercises():
    """Calculate all personalized exercises"""
    calculate_exercises()


@calc.command()
def clues():
    """Calculate all CLUes"""
    calculate_clues()


@calc.command()
@pass_context
def all(ctx):
    """Run all calculations once"""
    for command in calc.list_commands(ctx):
        if command != 'all':
            calc.get_command(ctx, command).invoke(ctx)
