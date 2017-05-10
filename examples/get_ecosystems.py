import json
import requests
import uuid

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

    def chunkify(lst, size):
        for ii in range(0, len(lst), size):
            yield lst[ii:ii + size]

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
                'max_num_events': 10,
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

            # import pdb; pdb.set_trace()


if __name__ == '__main__':
    fetch_ecosystem_metadata()
