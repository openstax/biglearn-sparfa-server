import logging
from sqlalchemy import select, func
from sqlalchemy.dialects.postgresql import (
    ARRAY,
    insert,
    JSON,
    UUID
)
import sqlalchemy as sa

from .utils import Executor, make_database_url

__logs__ = logging.getLogger(__name__)

executor = Executor(make_database_url())

metadata = sa.MetaData()


@executor
def upsert_into(table, values):
    insert_stmt = insert(table).values(values)

    do_nothing_stmt = insert_stmt.on_conflict_do_nothing()
    __logs__.info(
        'Inserting into {0} {1} items {2:.150}'.format(table, len(values),
                                                       str(values)))
    return do_nothing_stmt


@executor
def get_ecosystem_by_id(ecosystem_id):
    return select([ecosystems]).where(
        ecosystems.c.id == ecosystem_id)


@executor
def select_by_id_or_uuid(table, **kwargs):
    query = select([table])
    id_val = kwargs.get('id', None)
    uuid_val = kwargs.get('uuid', None)
    if id_val:
        query = query.where(table.c.id == id_val)
    elif uuid_val:
        query = query.where(table.c.uuid == uuid_val)
    else:
        raise Exception(
            'A uuid value or an id value should be included as kwargs')
    return query


@executor
def get_ecosystem_by_uuid(ecosystem_uuid):
    return select([ecosystems]).where(
        ecosystems.c.uuid == ecosystem_uuid)


@executor(fetch_all=True)
def get_all_ecosystem_uuids():
    return select([ecosystems.c.uuid])


@executor
def select_max_sequence_offset(course_uuid):
    return select([func.max(course_events.c.sequence_number)]).where(
        course_events.c.course_uuid == course_uuid)


@executor(fetch_all=True)
def select_ecosystem_exercises(ecosystem_uuid):
    return select([ecosystem_exercises.c.exercise_uuid]).where(
        ecosystem_exercises.c.ecosystem_uuid == ecosystem_uuid)


@executor(fetch_all=True)
def select_ecosystem_containers(ecosystem_uuid):
    return select([containers]).where(
        containers.c.ecosystem_uuid == ecosystem_uuid)


@executor(fetch_all=True)
def select_ecosystem_responses(ecosystem_uuid):
    return select([responses]).where(
        responses.c.ecosystem_uuid == ecosystem_uuid)


@executor(fetch_all=True)
def select_exercise_page_modules(exercise_uuid, ecosystem_uuid):
    return select([container_exercises]).select_from(
        container_exercises.join(
            containers,
            container_exercises.c.container_uuid == containers.c.uuid)).where(
        container_exercises.c.exercise_uuid == exercise_uuid).where(
        containers.c.is_page_module == True).where(
        container_exercises.c.ecosystem_uuid == ecosystem_uuid)


def max_sequence_offset(course_uuid):
    cur_sequence_offset = select_max_sequence_offset(
        course_uuid).scalar()

    if not cur_sequence_offset:
        cur_sequence_offset = 0
    else:
        cur_sequence_offset += 1
    return cur_sequence_offset


ecosystems = sa.Table('ecosystems', metadata,
                      sa.Column('id', sa.Integer, primary_key=True),
                      sa.Column('uuid', UUID, nullable=False, unique=True)
                      )

exercises = sa.Table('exercises', metadata,
                     sa.Column('id', sa.Integer, primary_key=True),
                     sa.Column('uuid', UUID, unique=True),
                     sa.Column('group_uuid', UUID, nullable=False),
                     sa.Column('los', ARRAY(sa.String()), nullable=False),
                     sa.Column('version', sa.Integer, nullable=False)
                     )

containers = sa.Table('containers', metadata,
                      sa.Column('id',
                                sa.Integer,
                                primary_key=True),
                      sa.Column('uuid',
                                UUID,
                                unique=True),
                      sa.Column('ecosystem_uuid', UUID, nullable=False),
                      sa.Column('container_cnx_identity',
                                sa.String(50)),
                      sa.Column('container_parent_uuid',
                                UUID),
                      sa.Column('is_page_module', sa.Boolean, default=False,
                                nullable=False)
                      )

container_exercises = sa.Table('container_exercises', metadata,
                               sa.Column('id',
                                         sa.Integer,
                                         primary_key=True),
                               sa.Column('container_uuid',
                                         UUID,
                                         nullable=False,
                                         index=True),
                               sa.Column('exercise_uuid',
                                         UUID,
                                         nullable=False,
                                         index=True),
                               sa.Column('ecosystem_uuid',
                                         UUID,
                                         nullable=False),
                               sa.UniqueConstraint('container_uuid',
                                                   'ecosystem_uuid',
                                                   'exercise_uuid')
                               )

courses = sa.Table('courses', metadata,
                   sa.Column('id',
                             sa.Integer,
                             primary_key=True),
                   sa.Column('uuid',
                             UUID,
                             unique=True),
                   sa.Column('ecosystem_uuid',
                             UUID,
                             nullable=False)
                   )

course_events = sa.Table('course_events', metadata,
                         sa.Column('id',
                                   sa.Integer,
                                   primary_key=True),
                         sa.Column('event_type',
                                   sa.String(100),
                                   nullable=False),
                         sa.Column('uuid', UUID, unique=True),
                         sa.Column('course_uuid',
                                   UUID,
                                   nullable=False),
                         sa.Column('sequence_number',
                                   sa.Integer,
                                   nullable=False),
                         sa.Column('event_data', JSON, nullable=False)
                         )

ecosystem_exercises = sa.Table('ecosystem_exercises', metadata,
                               sa.Column('id',
                                         sa.Integer,
                                         primary_key=True),
                               sa.Column('ecosystem_uuid',
                                         UUID,
                                         nullable=False,
                                         index=True),
                               sa.Column('exercise_uuid',
                                         UUID,
                                         nullable=False),
                               sa.UniqueConstraint('ecosystem_uuid',
                                                   'exercise_uuid')
                               )

responses = sa.Table('responses', metadata,
                     sa.Column('id',
                               sa.Integer,
                               primary_key=True
                               ),
                     sa.Column('uuid',
                               UUID,
                               unique=True),
                     sa.Column('ecosystem_uuid',
                               UUID,
                               nullable=False,
                               index=True),
                     sa.Column('course_uuid',
                               UUID,
                               nullable=False),
                     sa.Column('exercise_uuid',
                               UUID,
                               nullable=False),
                     sa.Column('student_uuid',
                               UUID,
                               nullable=False),
                     sa.Column('is_correct',
                               sa.Boolean,
                               nullable=False)
                     )
