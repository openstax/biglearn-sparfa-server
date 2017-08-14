import logging

from sparfa_server.utils import make_database_url

from sparfa_server.dexecuter import Dexecuter
from sparfa_server.db import ( make_upsert_into_do_nothing_statement,
                              make_select_max_sequence_offset_statement )

from celery.signals import worker_process_init, worker_process_shutdown

dexecuter = Dexecuter(make_database_url())

__logs__ = logging.getLogger(__name__)


@worker_process_init.connect
def init_worker(**kwargs):
    print('Initializing database connection for worker.')
    db_conn = dexecuter.connect()


@worker_process_shutdown.connect
def shutdown_worker(**kwargs):
    print('Closing database connection for worker.')
    dexecuter.close()

@dexecuter
def upsert_into_do_nothing_with_existing(table, values):
    __logs__.info(
        'Inserting into {0} {1} items {2:.150}'.format(table, len(values),
                                                       str(values)))
    return make_upsert_into_do_nothing_statement(table, values)


@dexecuter
def select_max_sequence_offset_with_existing(course_uuid):
    return make_select_max_sequence_offset_statement(course_uuid)


def max_sequence_offset_with_existing(course_uuid):
    cur_sequence_offset = select_max_sequence_offset_with_existing(
        course_uuid).scalar()

    if not cur_sequence_offset:
        cur_sequence_offset = 0
    else:
        cur_sequence_offset += 1
    return cur_sequence_offset

