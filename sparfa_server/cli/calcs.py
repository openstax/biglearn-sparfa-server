from logging import getLogger

from click import group

from ..tasks.calcs import (calculate_ecosystem_matrices as calculate_ecosystem_matrices_task,
                           calculate_exercises as calculate_exercises_task,
                           calculate_clues as calculate_clues_task)


@group()
def calcs():
    """Manage Calculations"""


@calcs.command()
def calculate_ecosystem_matrices():
    """Calculate all ecosystem matrices"""
    calculate_ecosystem_matrices_task.delay()


@calcs.command()
def calculate_exercises():
    """Calculate all personalized exercises"""
    calculate_exercises_task.delay()


@calcs.command()
def calculate_clues():
    """Calculate all CLUes"""
    calculate_clues_task.delay()


@calcs.command()
@pass_context
def calculate_all(ctx):
    """Run all calculations once"""
    for command in calcs.list_commands(ctx):
        calcs.get_command(ctx, command).invoke(ctx)
