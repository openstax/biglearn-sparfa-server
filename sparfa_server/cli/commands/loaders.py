import click

from sparfa_server.api import fetch_pending_ecosystems, fetch_course_uuids
from sparfa_server.loaders import (load_ecosystem as import_ecosystem,
                                   load_course as import_course,
                                   run as run_loaders)

from sparfa_server.tasks.calcs import run_matrix_calc_task
from sparfa_server.tasks.loaders import load_course_task, load_ecosystem_task

from sparfa_server.utils import validate_uuid4

import logging

logging.basicConfig(level=logging.INFO)
__logs__ = logging.getLogger(__name__)


@click.group()
def loaders():
    """Manage Loaders"""


@loaders.command()
@click.option('--ecosystem_uuid', prompt=True, help="The uuid of the ecosystem")
def load_ecosystem(ecosystem_uuid):
    """
    Load an ecosystem.
    """
    error_msg = 'An invalid ecosystem UUID was provided.'
    __logs__.info('Loading ecosystem UUID {0}'.format(ecosystem_uuid))
    if validate_uuid4(ecosystem_uuid):
        import_ecosystem(ecosystem_uuid)
    else:
        click.echo(error_msg)


@loaders.command()
@click.option('--course_uuid', prompt=True, help="The uuid of the course")
@click.option('--offset', type=int, default=None,
                                        help="The offset to start with. Loader will start with most recently recorded sequence number if omitted.")
@click.option('--step_size', type=int, default=1,
                                        help="Step size to increase by when gap exists.")
def load_course(course_uuid, offset, step_size):
    """
    Load a course
    """
    click.echo('Loading course UUID {0}'.format(course_uuid))
    if validate_uuid4(course_uuid):
        import_course(course_uuid, cur_sequence_offset=offset, sequence_step_size=step_size)
    else:
        click.echo('Please enter a valid UUID')


@loaders.command()
def load_ecosystems():
    ecosystem_uuids = fetch_pending_ecosystems()

    for eco_uuid in ecosystem_uuids:
        load_ecosystem_task.delay(eco_uuid)

    __logs__.info('Ecosystems have been loaded')


@loaders.command()
def load_courses():
    api_course_uuids = fetch_course_uuids()
    for course_uuid in api_course_uuids:
        load_course_task.delay(course_uuid, cur_sequence_offset = 0)

    run_matrix_calc_task.delay()
    __logs__.info('Initial courses and calculation tasks have been loaded')


@loaders.command()
def all():
    ecosystem_uuids = fetch_pending_ecosystems()
    api_course_uuids = fetch_course_uuids()

    for eco_uuid in ecosystem_uuids:
        import_ecosystem(eco_uuid)
    for course_uuid in api_course_uuids:
        load_course_task.delay(course_uuid, cur_sequence_offset = 0)

    __logs__.info('Ecosystems and Courses have been loaded')


@loaders.command()
@click.option('--delay', type=int,
              help="Run loaders for all ecosystems and courses continuously.")
def run(delay):
    try:
        run_loaders(delay)
    except (KeyboardInterrupt, SystemExit):
        pass
