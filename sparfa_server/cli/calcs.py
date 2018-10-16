from click import group

from ..tasks.calcs import (calculate_ecosystem_matrices,
                           calculate_exercises,
                           calculate_clues)


@group()
def calc():
    """Run calculations."""


calc.command(name='ecosystem_matrices')(calculate_ecosystem_matrices)
calc.command(name='exercises')(calculate_exercises)
calc.command(name='clues')(calculate_clues)


@calc.command()
def all():
    """Run all calculations once"""
    calculate_ecosystem_matrices()
    calculate_exercises()
    calculate_clues()
