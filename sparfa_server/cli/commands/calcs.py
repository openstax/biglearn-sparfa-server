import click

from celery import group
from sparfa_server.tasks.calcs import (run_matrix_calc_task,
                                       run_pe_calc_task,
                                       run_clue_calc_task,
                                       run_matrix_all_ecosystems_task,
                                       run_pe_calc_recurse_task,
                                       run_clue_calc_recurse_task)

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
def calc_all_ecosystem_matrix():
    """
    Calculate all ecosystem matrices
    """
    run_matrix_all_ecosystems_task.delay()
    __logs__.info('Initial ecosystem calculations running for all ecosystems')


@calcs.command()
def calc_pes():
    """
    Calculate PEs
    """
    run_pe_calc_task.delay()
    __logs__.info('Initial ecosystem calculations running')


@calcs.command()
def calc_clues():
    """
    Calculate CLUEs
    """
    run_clue_calc_task.delay()
    __logs__.info('Initial ecosystem calculations running')


@calcs.command()
def calc_initial():
    """
    Calculate all queued up calculations
    """
    all_calcs = (run_matrix_all_ecosystems_task | group(run_pe_calc_recurse_task, run_clue_calc_recurse_task))
    all_calcs.delay()
