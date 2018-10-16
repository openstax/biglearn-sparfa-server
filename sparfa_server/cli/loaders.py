from click import group, pass_context

from ..tasks.loaders import (load_ecosystem_metadata,
                             load_ecosystem_events,
                             load_course_metadata,
                             load_course_events)


@group()
def load():
    """Run Loaders."""


@load.command()
def ecosystem_metadata():
    """Load all ecosystem metadata"""
    load_ecosystem_metadata()


@load.command()
def ecosystem_events():
    """Load all ecosystem events"""
    load_ecosystem_events()


@load.command()
def course_metadata():
    """Load all course metadata"""
    load_course_metadata()


@load.command()
def course_events():
    """Load all course events"""
    load_course_events()


@load.command()
@pass_context
def all(ctx):
    """Run all loaders once"""
    for command in load.list_commands(ctx):
        if command != 'all':
            load.get_command(ctx, command).invoke(ctx)
