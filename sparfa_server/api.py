import logging
import os
import uuid

from .client import BiglearnApi
from .db import get_all_ecosystem_uuids, get_all_course_uuids

__logs__ = logging.getLogger(__name__)

try:
    api_token = os.environ['BIGLEARN_API_TOKEN']
    sched_token = os.environ['BIGLEARN_SCHED_TOKEN']
except KeyError:
    raise Exception('Have you set env vars for biglearn tokens?')

blapi = BiglearnApi(api_token=api_token, sched_token=sched_token)


def create_course_event(course_uuid,
                        offset,
                        max_events,
                        request_uuid=None):

    if not request_uuid:
        request_uuid = str(uuid.uuid4())

    event_request = {
        'request_uuid': request_uuid,
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

    return event_request


def create_course_event_request(course_uuid,
                                offset,
                                max_events,
                                request_uuid=None):
    data = {
        'course_event_requests': [create_course_event(course_uuid,
                                                      offset,
                                                      max_events,
                                                      request_uuid=request_uuid)],
    }

    return data


def create_ecosystem_event_request(ecosystem_uuid, request_uuid=None):
    data = {
        'ecosystem_event_requests': [],
    }

    if not request_uuid:
        request_uuid = str(uuid.uuid4())

    event_request = {
        'request_uuid': request_uuid,
        'event_types': ['create_ecosystem'],
        'ecosystem_uuid': ecosystem_uuid,
        'sequence_number_offset': 0,
        'max_num_events': 10,
    }

    data['ecosystem_event_requests'].append(event_request)

    return data


def create_courses_event_request(courses_data, max_events):

    data = {
        'course_event_requests':
            [create_course_event(course['course_uuid'], course['sequence_offset'], max_events) for course in courses_data]
    }

    return data


def fetch_course_uuids(course_uuids=None):
    __logs__.info('Polling courses endpoint for new courses')
    course_metadatas = blapi.fetch_course_metadatas()
    if course_uuids:
        return [uuid['uuid'] for uuid in course_metadatas['course_responses'] if
                uuid in course_uuids]

    return [uuid['uuid'] for uuid in course_metadatas['course_responses']]


def fetch_pending_courses_metadata(force=False):
    __logs__.info('Polling courses endpoint for new courses')
    api_course_metadatas = blapi.fetch_course_metadatas()

    db_course_uuids = get_all_course_uuids()

    import_course_uuids = list(
        filter(lambda x: x['uuid'] not in db_course_uuids,
               api_course_metadatas))

    if force:
        import_course_uuids = api_course_metadatas

    return import_course_uuids


def fetch_course_event_requests(course_uuid, offset=0, max_events=100):
    payload = create_course_event_request(course_uuid, offset, max_events)

    course_event_reqs = blapi.fetch_course_event_requests(payload)

    course_event_resps = course_event_reqs['course_event_responses'][0]
    return course_event_resps


def fetch_pending_course_events_requests(current_course_events_data, max_events=100):
    payload = create_courses_event_request(current_course_events_data, max_events)

    course_event_reqs = blapi.fetch_course_event_requests(payload)

    course_event_resps = course_event_reqs['course_event_responses']
    return course_event_resps


def fetch_ecosystem_uuids(ecosystem_uuids=None):
    ecosystem_metadatas = blapi.fetch_ecosystem_metadatas()
    if ecosystem_uuids:
        return [uuid['uuid'] for uuid in
                ecosystem_metadatas['ecosystem_responses'] if
                uuid in ecosystem_uuids]
    else:
        return [uuid['uuid'] for uuid in
                ecosystem_metadatas['ecosystem_responses']]


def fetch_ecosystem_event_requests(ecosystem_uuid):
    payload = create_ecosystem_event_request(ecosystem_uuid)

    eco_event_reqs = blapi.fetch_ecosystem_event_requests(payload)

    eco_event_resps = eco_event_reqs['ecosystem_event_responses'][0]
    eco_data = eco_event_resps['events'][0]['event_data']

    contents_data = eco_data['book']['contents']
    exercises_data = eco_data['exercises']

    return contents_data, exercises_data


def fetch_matrix_calculations(algorithm_name):
    payload = dict(algorithm_name=algorithm_name)

    matrix_calcs_response = blapi.fetch_matrix_calcs(payload)
    matrix_calcs = matrix_calcs_response['ecosystem_matrix_updates']

    return matrix_calcs


def update_matrix_calculations(algorithm_name, calc_uuid):
    # TODO: add log message that update_matrix_calc is happening
    payload = {
        'ecosystem_matrices_updated': [
            {
                'calculation_uuid': calc_uuid,
                'algorithm_name': algorithm_name,
            },
        ],
    }

    response = blapi.update_matrix_calcs(payload)
    return response


def fetch_pending_ecosystems(force=False):
    __logs__.info('Polling ecosystem endpoint for new ecosystems')
    api_ecosystem_uuids = fetch_ecosystem_uuids()

    db_ecosystem_uuids = get_all_ecosystem_uuids()

    import_ecosystem_uuids = list(
        filter(lambda x: x not in db_ecosystem_uuids,
               api_ecosystem_uuids))

    if force:
        import_ecosystem_uuids = api_ecosystem_uuids

    return import_ecosystem_uuids


def fetch_exercise_calcs(alg_name):
    # TODO: add log message that update_matrix_calc is happening
    payload = dict(
        algorithm_name=alg_name
    )

    response = blapi.fetch_exercise_calcs(payload)

    exercise_calcs = response['exercise_calculations']
    return exercise_calcs


def update_exercise_calcs(alg_name, calc_uuid, exercise_uuids):
    payload = {
        'exercise_calculation_updates': [
            {
                'calculation_uuid': calc_uuid,
                'algorithm_name': alg_name,
                'exercise_uuids': exercise_uuids
            }
        ]
    }
    response = blapi.update_exercise_calcs(payload)
    return response['exercise_calculation_update_responses'][0]


def fetch_clue_calcs(alg_name):
    payload = dict(
        algorithm_name=alg_name
    )

    response = blapi.fetch_clue_calcs(payload)

    clue_calcs = response['clue_calculations']
    return clue_calcs


def update_clue_calcs(alg_name, ecosystem_uuid, calc_uuid, clue_min,
                      clue_most_likely, clue_max, clue_is_real):
    payload = {
        'clue_calculation_updates': [
            {
                'calculation_uuid': calc_uuid,
                'algorithm_name': alg_name,
                'clue_data': {
                    'ecosystem_uuid': ecosystem_uuid,
                    'minimum': clue_min,
                    'most_likely': clue_most_likely,
                    'maximum': clue_max,
                    'is_real': clue_is_real
                }
            }
        ]
    }
    response = blapi.update_clue_calcs(payload)
    return response['clue_calculation_update_responses'][0]

