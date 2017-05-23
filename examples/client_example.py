# Checklist
# [X] Create basic client to start working with responses
# [X] Need to get all the ecosystems
# [ ] Save all ecosystems to the database
# [ ] Need to get all responses
# [ ] Ask BL Scheduler server what needs to be updated
# [X] Refactor biglearn client
# [ ] Compute all the things

import json
import logging

from sparfa_server.api import (fetch_ecosystem_uuids,
                               fetch_ecosystem_event_requests)

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)


def write_json_file(filename, data):
    with open(filename + '.json', 'w') as outfile:
        json.dump(data, outfile, sort_keys=True, indent=4)


def main():
    create_ecosystem_files = False
    fetch_course_files = False

    if create_ecosystem_files:
        ecosystem_uuids = fetch_ecosystem_uuids()
        for ecosystem_uuid in ecosystem_uuids[:1]:
            eco_event_reqs = fetch_ecosystem_event_requests(ecosystem_uuid)

            write_json_file('output/ecosystem_{}'.format(ecosystem_uuid),
                            eco_event_reqs)

    with open('output/ecosystem_f667f783-7944-4153-81ee-f245c209f406.json') as infile:
        data = json.load(infile)

    eco_event_responses = data['ecosystem_event_responses'][0]

    events = eco_event_responses['events']

    print(events)




if __name__ == '__main__':
    main()
