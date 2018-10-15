from click import group, option, echo

from ..api import fetch_pending_ecosystems, fetch_course_uuids
from ..tasks.loaders import (load_ecosystem_metadata as load_ecosystem_metadata_task,
                             load_ecosystem_events as load_ecosystem_events_task,
                             load_course_metadata as load_course_metadata_task,
                             load_course_events as load_course_events_task)


@group()
def loaders():
    """Manage Loaders"""


@loaders.command()
def load_ecosystem_metadata():
    """Load all ecosystem metadata"""
    load_ecosystem_metadata_task.delay()


@loaders.command()
def load_ecosystem_events():
    """Load all ecosystem events"""
    load_ecosystem_events_task.delay()


@loaders.command()
def load_course_metadata():
    """Load all course metadata"""
    load_course_metadata_task.delay()


@loaders.command()
def load_course_events():
    """Load all course events"""
    load_course_events_task.delay()


@loaders.command()
@pass_context
def load_all(ctx):
    """Run all loaders once"""
    for command in loaders.list_commands(ctx):
        loaders.get_command(ctx, command).invoke(ctx)
