from click import group

from ..tasks.loaders import (load_ecosystem_metadata,
                             load_ecosystem_events,
                             load_course_metadata,
                             load_course_events)


@group()
def load():
    """Run loaders."""


@load.group()
def ecosystem():
    """Run ecosystem loaders."""


ecosystem.command(name='metadata')(load_ecosystem_metadata)
ecosystem.command(name='events')(load_ecosystem_events)


@ecosystem.command(name='both')
def ecosystem_both():
    """Run both ecosystem loaders"""
    load_ecosystem_metadata()
    load_ecosystem_events()


@load.group()
def course():
    """Run course loaders."""


course.command(name='metadata')(load_course_metadata)
course.command(name='events')(load_course_events)


@course.command(name='both')
def course_both():
    """Run both course loaders"""
    load_course_metadata()
    load_course_events()


@load.command()
def all():
    """Run all loaders once"""
    load_ecosystem_metadata()
    load_ecosystem_events()
    load_course_metadata()
    load_course_events()
