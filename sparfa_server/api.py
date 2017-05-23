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
    return [id['uuid'] for id in ecosystem_metadatas['ecosystem_responses']]


def fetch_ecosystem_event_requests(ecosystem_uuid):
    payload = create_ecosystem_event_request(ecosystem_uuid)
    event_requests = blapi.fetch_ecosystem_event_requests(payload)
    return event_requests
