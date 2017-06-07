import uuid

from .client import BiglearnApi

blapi = BiglearnApi()


def create_course_event_request(course_uuid, offset, max_events):
    data = {
        'course_event_requests': [],
    }

    event_request = {
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
            'record_response'
        ],
        'course_uuid': course_uuid,
        'sequence_number_offset': offset,
        'max_num_events': max_events
    }

    data['course_event_requests'].append(event_request)
    return data


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


def fetch_course_uuids():
    course_metadatas = blapi.fetch_course_metadatas()
    return [uuid['uuid'] for uuid in course_metadatas['course_responses']]


def fetch_course_event_requests(course_uuid, offset=0, max_events=100):
    payload = create_course_event_request(course_uuid, offset, max_events)

    course_event_reqs = blapi.fetch_course_event_requests(payload)

    course_event_resps = course_event_reqs['course_event_responses'][0]
    return course_event_resps


def fetch_ecosystem_uuids():
    ecosystem_metadatas = blapi.fetch_ecosystem_metadatas()
    return [uuid['uuid'] for uuid in ecosystem_metadatas['ecosystem_responses']]


def fetch_ecosystem_event_requests(ecosystem_uuid):
    payload = create_ecosystem_event_request(ecosystem_uuid)

    eco_event_reqs = blapi.fetch_ecosystem_event_requests(payload)

    eco_event_resps = eco_event_reqs['ecosystem_event_responses'][0]
    eco_data = eco_event_resps['events'][0]['event_data']
    return eco_data
