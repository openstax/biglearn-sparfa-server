import json
import logging

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy import select

from sparfa_server.api import (
    fetch_ecosystem_uuids,
    fetch_ecosystem_event_requests)
from sparfa_server.models import ecosystems, books, chapters
from sparfa_server.utils import Executor, make_database_url

logging.basicConfig(level=logging.DEBUG)
__logs__ = logging.getLogger(__name__)

connection_string = make_database_url()

executor = Executor(connection_string)


def write_json_file(filename, data):
    with open(filename + '.json', 'w') as outfile:
        json.dump(data, outfile, sort_keys=True, indent=4)


@executor
def upsert_into(table, values):
    insert_stmt = insert(table).values(values)

    do_nothing_stmt = insert_stmt.on_conflict_do_nothing(
        index_elements=['uuid']
    )
    __logs__.debug('Inserting into {0} with item {1}'.format(table, values))
    return do_nothing_stmt


@executor
def get_ecosystem_by_id(ecosystem_id):
    return select([ecosystems]).where(
        ecosystems.c.id == ecosystem_id)


@executor
def select_by_uuid(table, uuid_val):
    return select([table]).where(table.c.uuid == uuid_val)


@executor
def get_ecosystem_by_uuid(ecosystem_uuid):
    return select([ecosystems]).where(
        ecosystems.c.uuid == ecosystem_uuid)


@executor(fetch_all=True)
def get_all_ecosystem_uuids():
    return select([ecosystems.c.uuid])


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

    if row.inserted_primary_key:
        return row.inserted_primary_key[0]
    else:
        r = select_by_uuid(table, values['uuid']).fetchone()
        return r['id']


def main():
    # Setting for forcing the insert/update of the ecosystems
    force_update = True

    # All ecosystem uuids from the biglearn api
    api_ecosystem_uuids = fetch_ecosystem_uuids()

    # All ecosystem uuids from the database
    db_ecosystem_uuids = get_all_ecosystem_uuids()

    if force_update:
        import_ecosystem_uuids = api_ecosystem_uuids
    else:
        # Filter only the ecosystems that need to be imported
        import_ecosystem_uuids = list(
            filter(lambda x: x not in db_ecosystem_uuids,
                   api_ecosystem_uuids))

    for eco_uuid in import_ecosystem_uuids:
        __logs__.debug(
            'Ecosystem {} not found in the database. importing ...'.format(
                eco_uuid))

        # Upsert the ecosystem record
        ecosystem_id = upsert_and_return_id(ecosystems, dict(uuid=eco_uuid))

        # Retrieve ecosystem data (book and content) and import those
        ecosystem_data = fetch_ecosystem_event_requests(eco_uuid)

        book_data = ecosystem_data['book']

        book_values = dict(
            uuid=book_data['cnx_identity'].split('@')[0],
            ecosystem_id=ecosystem_id
        )

        book_id = upsert_and_return_id(books, book_values)

        contents_data = book_data['contents']

        for container in contents_data:
            content_values = dict(
                uuid=container['container_uuid'],
                container_parent_uuid=container['container_parent_uuid'],
                container_cnx_identity=container['container_cnx_identity']
            )
            content_id = upsert_and_return_id(chapters, content_values)

            pools = container['pools']




if __name__ == '__main__':
    main()
