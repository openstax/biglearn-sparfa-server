import click

from celery import group
from sparfa_server.tasks.calcs import (run_matrix_calcs_task,
                                       run_pe_calcs_task,
                                       run_clue_calcs_task,
                                       run_matrix_all_ecosystems_task,
                                       run_pe_calcs_recurse_task,
                                       run_clue_calcs_recurse_task)

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
    run_matrix_calcs_task.delay()
    __logs__.info('Initial ecosystem calculations running')


@calcs.command()
def calc_all_ecosystem_matrix():
    """
    Calculate all ecosystem matrices
    """
    __logs__.info('Initial ecosystem calculations running for all ecosystems')
    run_matrix_all_ecosystems_task.delay()


@calcs.command()
def calc_pes():
    """
    Calculate PEs
    """
    run_pe_calcs_task.delay()
    __logs__.info('Initial ecosystem calculations running')


@calcs.command()
def calc_clues():
    """
    Calculate CLUEs
    """
    run_clue_calcs_task.delay()
    __logs__.info('Initial ecosystem calculations running')


@calcs.command()
def calc_clue_initial():
    run_clue_calcs_recurse_task.delay()


@calcs.command()
def calc_pe_initial():
    run_pe_calcs_recurse_task.delay()


@calcs.command()
def calc_initial():
    """
    Calculate all queued up calculations
    """
    all_calcs = (run_matrix_all_ecosystems_task.si() | group(run_pe_calcs_recurse_task.si(), run_clue_calcs_recurse_task.si()))
    all_calcs.delay()
