import logging
from sqlalchemy import select, func
from sqlalchemy.dialects.postgresql import (ARRAY,
                                            insert,
                                            JSON,
                                            UUID)
import sqlalchemy as sa

from .utils import Executor, make_database_url

__logs__ = logging.getLogger(__name__)

executor = Executor(make_database_url())

metadata = sa.MetaData()


@executor
def upsert_into(table, values):
    insert_stmt = insert(table).values(values)

    do_nothing_stmt = insert_stmt.on_conflict_do_nothing()
    __logs__.info('Inserting into {0} with item {1}'.format(table, values))
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
    return select([func.max(course_events.c.sequence_number)]).select_from(
        course_events.join(courses,
                           courses.c.id == course_events.c.course_id)).where(
        courses.c.uuid == course_uuid)


def upsert_and_return_id(table, values):
    """
    A special upsert that inserts a new row in the database if there is
    no conflict. When a successful insert occurs the `inserted_primary_key`
    is returned. In the situation a conflict does occur due to a unique
    value constraint the insert does nothing and the function "looks up"
    and returns the primary key that is needed.

    This function is necessary due to the `inserted_primary_key`
    attribute on the `ResultProxy` not containing a value when the upsert
    encounters a conflict.

    :param table:
    :param values:
    :return:
    """
    row = upsert_into(table, values)
    if row.lastrowid != 0:
        return row.inserted_primary_key
    else:
        if isinstance(values, dict):
            r = select_by_id_or_uuid(table, **values).fetchone()
            return r['id']
        elif isinstance(values, list):
            r = [select_by_id_or_uuid(table, **val).fetchone()['id'] for val in
                 values]
            return r


ecosystems = sa.Table('ecosystems', metadata,
                      sa.Column('id', sa.Integer, primary_key=True),
                      sa.Column('uuid', UUID, nullable=False, unique=True)
                      )

exercises = sa.Table('exercises', metadata,
                     sa.Column('id', sa.Integer, primary_key=True),
                     sa.Column('uuid', UUID, unique=True)
                     )

books = sa.Table('books', metadata,
                 sa.Column('id',
                           sa.Integer,
                           primary_key=True),
                 sa.Column('uuid',
                           UUID,
                           nullable=False,
                           unique=True),
                 sa.Column('ecosystem_id',
                           None,
                           sa.ForeignKey('ecosystems.id'))
                 )

containers = sa.Table('containers', metadata,
                      sa.Column('id',
                                sa.Integer,
                                primary_key=True),
                      sa.Column('uuid',
                                UUID,
                                unique=True),
                      sa.Column('book_id',
                                None,
                                sa.ForeignKey('books.id')),
                      sa.Column('container_cnx_identity',
                                sa.String(50)),
                      sa.Column('container_parent_uuid',
                                UUID)
                      )

ecosystem_pools = sa.Table('ecosystem_pools', metadata,
                           sa.Column('id',
                                     sa.Integer,
                                     primary_key=True),
                           sa.Column('ecosystem_id',
                                     sa.Integer,
                                     nullable=False),
                           sa.Column('exercise_uuids',
                                     ARRAY(sa.String())),
                           sa.Column('container_id',
                                     sa.Integer,
                                     sa.ForeignKey('containers.id'))
                           )

courses = sa.Table('courses', metadata,
                   sa.Column('id',
                             sa.Integer,
                             primary_key=True),
                   sa.Column('uuid',
                             UUID,
                             unique=True),
                   sa.Column('ecosystem_id',
                             None,
                             sa.ForeignKey('ecosystems.id')),
                   )

course_events = sa.Table('course_events', metadata,
                         sa.Column('id',
                                   sa.Integer,
                                   primary_key=True),
                         sa.Column('event_type',
                                   sa.String(100),
                                   nullable=False),
                         sa.Column('uuid', UUID, unique=True),
                         sa.Column('course_id',
                                   None,
                                   sa.ForeignKey('courses.id')),
                         sa.Column('sequence_number',
                                   sa.Integer,
                                   nullable=False),
                         sa.Column('event_data', JSON, nullable=False)
                         )

ecosystem_exercises = sa.Table('ecosystem_exercises', metadata,
                               sa.Column('id',
                                         sa.Integer,
                                         primary_key=True),
                               sa.Column('container_id',
                                         None,
                                         sa.ForeignKey('containers.id')),
                               sa.Column('ecosystem_id',
                                         None,
                                         sa.ForeignKey('ecosystems.id')),
                               sa.Column('exercise_id',
                                         None,
                                         sa.ForeignKey('exercises.id'))
                               )

responses = sa.Table('responses', metadata,
                     sa.Column('id',
                               sa.Integer,
                               primary_key=True
                               ),
                     sa.Column('uuid',
                               UUID,
                               unique=True),
                     sa.Column('ecosystem_id',
                               None,
                               sa.ForeignKey('ecosystems.id')),
                     sa.Column('course_id',
                               None,
                               sa.ForeignKey('courses.id')
                               ),
                     sa.Column('exercise_id',
                               None,
                               sa.ForeignKey('exercises.id')),
                     sa.Column('student_uuid',
                               UUID,
                               nullable=False),
                     sa.Column('is_correct',
                               sa.Boolean,
                               nullable=False)
                     )
