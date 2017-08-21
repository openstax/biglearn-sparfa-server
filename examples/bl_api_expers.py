import json
import requests
import time
import uuid


def chunkify(lst, size):
    for ii in range(0, len(lst), size):
        yield lst[ii:ii + size]


## NOTE: These names might change in the near future.
bl_api_base = 'https://biglearn-dev.openstax.org'
bl_scheduler_base = 'https://biglearnworker-dev.openstax.org'


def fetch_ecosystem_metadata():
    metadata_response = requests.post(
        bl_api_base + '/fetch_ecosystem_metadatas',
        headers={'Content-Type': 'application/json'},
        data=json.dumps({}),
    )

    if not metadata_response.status_code == 200:
        raise Exception('problem fetching ecosystem metadata: {}'.format(
            metadata_response.status_code
        ))

    # import pdb; pdb.set_trace()

    chunks = chunkify(
        lst=metadata_response.json()['ecosystem_responses'],
        size=1,
    )

    for metadata_response_chunk in chunks:
        ecosystem_uuids = map(lambda xx: xx['uuid'], metadata_response_chunk)

        data = {
            'ecosystem_event_requests': [],
        }

        for ecosystem_uuid in ecosystem_uuids:
            event_request = {
                'request_uuid': str(uuid.uuid4()),
                'event_types': ['create_ecosystem'],
                'ecosystem_uuid': ecosystem_uuid,
                'sequence_number_offset': 0,
            }

            data['ecosystem_event_requests'].append(event_request)

        # import pdb; pdb.set_trace()

        chunk_response = requests.post(
            bl_api_base + '/fetch_ecosystem_events',
            headers={'Content-Type': 'application/json'},
            data=json.dumps(data),
        )

        with open('output/ecosystem_{}.txt'.format(ecosystem_uuid), 'w') as fd:
            pretty_str = json.dumps(chunk_response.json(), indent=4,
                                    sort_keys=True)
            fd.write(pretty_str)

        # import pdb;
        # pdb.set_trace()


def fetch_course_uuids():
    metadata_response = requests.post(
        bl_api_base + '/fetch_course_metadatas',
        headers={'Content-Type': 'application/json'},
        data=json.dumps({}),
    )

    if not metadata_response.status_code == 200:
        raise Exception('problem fetching course metadata: {}'.format(
            metadata_response.status_code
        ))

    course_uuids = map(lambda xx: xx['uuid'],
                       metadata_response.json()['course_responses'])

    return course_uuids


def fetch_course_events(target_course_uuid):
    start_time = time.time()

    with open('output/course_{}.txt'.format(target_course_uuid), 'w') as fd:
        current_sequence_number = 0

        while True:
            data = {
                'course_event_requests': [
                    {
                        'request_uuid': str(uuid.uuid4()),
                        'event_types': [
                            'create_course',
                            'prepare_course_ecosystem',
                            'update_course_ecosystem',
                            'update_roster',
                            'update_course_active_dates',
                            'update_globally_excluded_exercises',
                            'update_course_excluded_exercises',
                            'create_update_assignment',
                            'record_response',
                        ],
                        'course_uuid': target_course_uuid,
                        'sequence_number_offset': current_sequence_number,
                    },
                ],
            }

            time1 = time.time()
            response = requests.post(
                bl_api_base + '/fetch_course_events',
                headers={'Content-Type': 'application/json'},
                data=json.dumps(data),
            )
            time2 = time.time()
            print('  call: {:1.3e}'.format(time2 - time1))

            if not response.status_code == 200:
                raise Exception('problem fetching course events: {}'.format(
                    response.status_code
                ))

            pretty_str = json.dumps(response.json(), indent=4, sort_keys=True)
            fd.write(pretty_str)
            fd.write('\n')

            response_json = response.json()['course_event_responses']
            if len(response_json) != 1:
                raise Exception(
                    'unexpected response length ({} != 1)'.format(
                        len(response_json)))
            response_json = response_json[0]

            num_fetched_events = len(response_json['events'])

            is_gap = response_json['is_gap']
            is_end = response_json['is_end']

            print('{:1.5e}: fetched {:3d} events ({} {} {})'.format(
                time.time() - start_time,
                num_fetched_events,
                is_gap,
                is_end,
                current_sequence_number
            ))

            if is_gap or is_end:
                break

            current_sequence_number += num_fetched_events

            # import pdb; pdb.set_trace()


if __name__ == '__main__':
    # fetch_ecosystem_metadata()
    course_uuids = list(fetch_course_uuids())
    fetch_course_events(target_course_uuid=course_uuids[0])
