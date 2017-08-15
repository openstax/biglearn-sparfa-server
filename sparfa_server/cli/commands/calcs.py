import click

from sparfa_server.tasks.calcs import run_matrix_calc_task

import logging

logging.basicConfig(level=logging.INFO)
__logs__ = logging.getLogger(__name__)


@click.group()
def calcs():
    """Manage Loaders"""


@calcs.command()
def calc_ecosystem_matrix(ecosystem_uuid):
    """
    Calculate all ecosystem matrices
    """
    run_matrix_calc_task.delay()
    __logs__.info('Initial ecosystem calculations running')

