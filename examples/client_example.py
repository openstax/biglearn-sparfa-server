# Checklist
# [X] Create basic client to start working with responses
# [X] Need to get all the ecosystems
# [ ] Need to get all responses
# [ ] Ask BL Scheduler server what needs to be updated
# [ ] Refactor biglearn client
# [ ] Compute all the things

import json
import uuid

from sparfa_server.client import Client


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
    api = Client()

    # retrieve all the ecosystems
    ecosystem_metadata = api.post('/fetch_ecosystem_metadatas')

    # parse out the ecosystem uuids
    ecosystem_uuids = [id['uuid'] for id in
                       ecosystem_metadata['ecosystem_responses']]

    # make a request for ecosystem events for each ecosystem uuid
    for ecosystem_uuid in ecosystem_uuids:
        event_request = create_ecosystem_event_request(ecosystem_uuid)

        ecosystem_events = api.post('/fetch_ecosystem_events', **event_request)
        print(ecosystem_events)

        write_json_file('output/ecosystem_{}'.format(ecosystem_uuid),
                        ecosystem_events)


if __name__ == '__main__':
    main()
