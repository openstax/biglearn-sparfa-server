import json
import logging

from sparfa_server.api import (
    fetch_ecosystem_uuids,
    fetch_ecosystem_event_requests)
from sparfa_server.models import (ecosystems,
                                  books,
                                  containers,
                                  ecosystem_pools,
                                  get_all_ecosystem_uuids,
                                  upsert_and_return_id, exercises, upsert_into,
                                  ecosystem_exercises)
from sparfa_server.utils import Executor, make_database_url

logging.basicConfig(level=logging.DEBUG)
__logs__ = logging.getLogger(__name__)


def write_json_file(filename, data):
    with open(filename + '.json', 'w') as outfile:
        json.dump(data, outfile, sort_keys=True, indent=4)


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
            container_values = dict(
                uuid=container['container_uuid'],
                container_parent_uuid=container['container_parent_uuid'],
                container_cnx_identity=container['container_cnx_identity'],
                book_id=book_id
            )
            container_id = upsert_and_return_id(containers, container_values)

            pools = container['pools']

            if pools:
                for pool in pools:
                    if pool['exercise_uuids']:
                        pool_values = dict(ecosystem_id=ecosystem_id,
                                           container_id=container_id,
                                           exercise_uuids=pool['exercise_uuids']
                                           )
                        upsert_into(ecosystem_pools,pool_values)



                        exercise_values = [dict(uuid=ex_uuid) for ex_uuid in
                                          pool['exercise_uuids']]

                        exercise_ids = upsert_and_return_id(exercises, exercise_values)
                        eco_exercises = []

                        for exercise_id in exercise_ids:
                            eco_exercise_values = dict(
                                ecosystem_id=ecosystem_id,
                                container_id=container_id,
                                exercise_id=exercise_id
                            )

                            eco_exercises.append(eco_exercise_values)

                        upsert_into(ecosystem_exercises, eco_exercises)


if __name__ == '__main__':
    main()
