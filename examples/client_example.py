# Checklist
# [X] Create basic client to start working with responses
# [X] Need to get all the ecosystems
# [ ] Need to get all responses
# [ ] Ask BL Scheduler server what needs to be updated
# [ ] Refactor biglearn client
# [ ] Compute all the things

import json
import os
import sys
import uuid

from os.path import dirname, abspath

sys.path.append(dirname(dirname(abspath(__file__))))
sys.path.append(os.getcwd())


from sparfa_server.client import BiglearnAPI


def create_ecosystem_event_request(ecosystem_uuid):
    data = {
        'ecosystem_event_requests': [],
    }

    event_request = {
        'request_uuid': str(uuid.uuid4()),
        'event_types': ['create_ecosystem'],
        'ecosystem_uuid': ecosystem_uuid,
        'sequence_number_offset': 0,
        'max_num_events': 10,
    }

    data['ecosystem_event_requests'].append(event_request)

    return data


def write_json_file(filename, data):
    with open(filename + '.json', 'w') as outfile:
        json.dump(data, outfile, sort_keys=True, indent=4)


def main():
    # Zend in ze Client!
    api = BiglearnAPI()

    # Enable if you don't have any ecosystem files in output.
    fetch_ecosystem_files = False

    if fetch_ecosystem_files:

        # retrieve all the ecosystems
        ecosystem_metadata = api.fetch_ecosystem_metadatas()

        # parse out the ecosystem uuids
        ecosystem_uuids = [id['uuid'] for id in
                           ecosystem_metadata['ecosystem_responses']]

        # make a request for ecosystem events for each ecosystem uuid
        for ecosystem_uuid in ecosystem_uuids:
            ecosystem_events = api.fetch_ecosystem_events(ecosystem_uuid)

            write_json_file('output/ecosystem_{}'.format(ecosystem_uuid),
                            ecosystem_events)




if __name__ == '__main__':
    main()
