from logging import getLogger

from click import group, option, echo

from ..api import fetch_pending_ecosystems, fetch_course_uuids
from ..tasks.loaders import (load_course_task,
                             load_ecosystem_task,
                             load_courses_task,
                             load_ecosystems_task,
                             load_courses_metadata_task,
                             load_courses_updates_task)

__logs__ = getLogger(__name__)

def _validate_uuid4(uuid_string):
    try:
        val = UUID(uuid_string, version=4)
    except ValueError:
        return False

    return val.hex == uuid_string.replace('-', '')


@group()
def loaders():
    """Manage Loaders"""


@loaders.command()
@option('--ecosystem_uuid', prompt=True, help="The uuid of the ecosystem")
def load_ecosystem(ecosystem_uuid):
    """
    Load an ecosystem.
    """
    error_msg = 'An invalid ecosystem UUID was provided.'
    __logs__.info('Loading ecosystem UUID {0}'.format(ecosystem_uuid))
    if _validate_uuid4(ecosystem_uuid):
        load_ecosystem_task.delay(ecosystem_uuid)
    else:
        echo(error_msg)


@loaders.command()
@option('--course_uuid', prompt=True, help="The uuid of the course")
@option('--offset', type=int, default=None,
                              help="The offset to start with. Loader will start with most recently recorded sequence number if omitted.")
@option('--step_size', type=int, default=1,
                                        help="Step size to increase by when gap exists.")
def load_course(course_uuid, offset, step_size):
    """
    Load a course
    """
    echo('Loading course UUID {0}'.format(course_uuid))
    if _validate_uuid4(course_uuid):
        load_course_task.delay(course_uuid, cur_sequence_offset=offset, sequence_step_size=step_size)
    else:
        echo('Please enter a valid UUID')


@loaders.command()
def load_ecosystems():
    load_ecosystems_task.delay()
    __logs__.info('Ecosystems have been loaded')


@loaders.command()
def load_courses():
    load_courses_task.delay()

    __logs__.info('Initial courses have been loaded')


@loaders.command()
def load_courses_metadata():
    load_courses_metadata_task.delay()

    __logs__.info('Load metadata for all courses')


@loaders.command()
def load_courses_updates():
    load_courses_updates_task.delay()

    __logs__.info('Latest courses have been loaded')


@loaders.command()
def all():
    load_ecosystems_task.delay()
    load_courses_task.delay()

    __logs__.info('Ecosystems and Courses have been loaded')


@loaders.command()
@option('--delay', type=int, help="Run loaders for all ecosystems and courses continuously.")
def run(delay):
    try:
        run_loaders(delay)
    except (KeyboardInterrupt, SystemExit):
        pass
