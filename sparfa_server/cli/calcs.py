from click import group

from ..tasks import calculate_ecosystem_matrices, calculate_exercises, calculate_clues


@group()
def calc():
    """Run calculations."""


calc.command(name='matrices')(calculate_ecosystem_matrices)
calc.command(name='exercises')(calculate_exercises)
calc.command(name='clues')(calculate_clues)


@calc.command()
def all():
    """Run all calculations once"""
    calculate_ecosystem_matrices()
    calculate_exercises()
    calculate_clues()
