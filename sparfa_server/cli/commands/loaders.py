import click
import click_log

from sparfa_server.api import fetch_pending_ecosystems, fetch_course_uuids
from sparfa_server.loaders import (load_ecosystem as import_ecosystem,
                                   load_course as import_course,
                                   run as run_loaders)

from sparfa_server.tasks import loaders as task_loaders
from sparfa_server.utils import validate_uuid4

import logging

__logs__ = logging.getLogger(__name__)


@click.group()
@click_log.simple_verbosity_option()
def loaders():
    """Manage Loaders"""


@loaders.command()
@click_log.simple_verbosity_option()
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
def load_course(course_uuid):
    """
    Load a course
    """
    click.echo('Loading course UUID {0}'.format(course_uuid))
    if validate_uuid4(course_uuid):
        import_course(course_uuid)
    else:
        click.echo('Please enter a valid UUID')


@loaders.command()
def all():
    ecosystem_uuids = fetch_pending_ecosystems()
    api_course_uuids = fetch_course_uuids()

    for eco_uuid in ecosystem_uuids:
        import_ecosystem(eco_uuid)
    for course_uuid in api_course_uuids:
        import_course(course_uuid)

    __logs__.info('Ecosystems and Courses have been loaded')


@loaders.command()
@click.option('--delay', type=int,
              help="Run loaders for all ecosystems and courses continuously.")
def run(delay):
    try:
        run_loaders(delay)
    except (KeyboardInterrupt, SystemExit):
        pass
