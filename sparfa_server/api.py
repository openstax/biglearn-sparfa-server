import uuid

from .client import BiglearnApi

blapi = BiglearnApi()


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


def fetch_ecosystem_uuids():
    ecosystem_metadatas = blapi.fetch_ecosystem_metadatas()
    return [uuid['uuid'] for uuid in ecosystem_metadatas['ecosystem_responses']]


def fetch_ecosystem_event_requests(ecosystem_uuid):
    payload = create_ecosystem_event_request(ecosystem_uuid)

    eco_event_reqs = blapi.fetch_ecosystem_event_requests(payload)

    eco_event_resps = eco_event_reqs['ecosystem_event_responses'][0]
    eco_data = eco_event_resps['events'][0]['event_data']
    return eco_data
