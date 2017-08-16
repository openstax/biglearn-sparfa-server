import click

from sparfa_server.tasks.calcs import (run_matrix_calc_task,
                                       run_pe_calc_task,
                                       run_clue_calc_task)

import logging

logging.basicConfig(level=logging.INFO)
__logs__ = logging.getLogger(__name__)


@click.group()
def calcs():
    """Manage Loaders"""


@calcs.command()
def calc_ecosystem_matrix():
    """
    Calculate all ecosystem matrices
    """
    run_matrix_calc_task.delay()
    __logs__.info('Initial ecosystem calculations running')


@calcs.command()
def calc_pes():
    """
    Calculate all PEs
    """
    run_pe_calc_task.delay()
    __logs__.info('Initial ecosystem calculations running')


@calcs.command()
def calc_clues():
    """
    Calculate all CLUEs
    """
    run_clue_calc_task.delay()
    __logs__.info('Initial ecosystem calculations running')

