import json
import logging

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy import select

from sparfa_server.api import (fetch_ecosystem_uuids,
                               fetch_ecosystem_event_requests)
from sparfa_server.models import ecosystems, books
from sparfa_server.utils import Executor, make_database_url, WorkerPool

logging.basicConfig(level=logging.DEBUG)
__logs__ = logging.getLogger(__name__)

connection_string = make_database_url()

executor = Executor(connection_string)


@executor
def upsert_into(table, values):
    insert_stmt = insert(table).values(values)

    do_nothing_stmt = insert_stmt.on_conflict_do_nothing(
        index_elements=['uuid']
    )
    __logs__.info('Inserting into {0} with item {1}'.format(table, values))
    return do_nothing_stmt


@executor
def get_ecosystem_by_id(ecosystem_id):
    return select([ecosystems]).where(
        ecosystems.c.id == ecosystem_id) @ executor


@executor
def get_ecosystem_by_uuid(ecosystem_uuid):
    return select([ecosystems]).where(
        ecosystems.c.uuid == ecosystem_uuid)


@executor(fetch_all=True)
def get_all_ecosystem_uuids():
    return select([ecosystems.c.uuid])


def get_ecosystem_data(ecosystem_uuid):
    """Takes the ecosystem uuid and imports the ecosystem information when
    an ecosystem is not found in the database.

    :param ecosystem_uuid: 
    :return: 
    """
    return fetch_ecosystem_event_requests(ecosystem_uuid)


def import_ecosystem_data(ecosystem_uuid):
    ecosystem_data = fetch_ecosystem_event_requests(ecosystem_uuid)
    eco = get_ecosystem_by_uuid(ecosystem_uuid)
    eco = eco.fetchone()
    book = ecosystem_data['book']
    book_data = dict(uuid=book['cnx_identity'].split('@')[0],
                     ecosystem_id=eco['id']
                     )
    stmt = upsert_into(books, book_data)


def main():
    pool = WorkerPool()
    pool.start()

    # All ecosystem uuids from the biglearn api
    api_ecosystem_uuids = fetch_ecosystem_uuids()

    # All ecosystem uuids from the database
    db_ecosystem_uuids = get_all_ecosystem_uuids()

    # Filter only the ecosystems that need to be imported
    import_ecosystem_uuids = list(filter(lambda x: x not in db_ecosystem_uuids,
                                         api_ecosystem_uuids))

    for eco_uuid in import_ecosystem_uuids:
        __logs__.debug(
            'Ecosystem {} not found in the database. importing ...'.format(
                eco_uuid))

        # Insert the ecosystem to the database
        pool.add_task(upsert_into, ecosystems, dict(uuid=eco_uuid))

        pool.add_task(import_ecosystem_data, eco_uuid)


if __name__ == '__main__':
    main()
