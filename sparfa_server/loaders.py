import logging

from sparfa_server.utils import delay

from .api import (
    fetch_ecosystem_event_requests,
    fetch_course_event_requests,
    fetch_pending_ecosystems,
    fetch_course_uuids)
from .models import (
    upsert_into,
    ecosystems,
    exercises,
    ecosystem_exercises,
    container_exercises,
    containers,
    responses,
    course_events,
    courses)
from .models import max_sequence_offset

__logs__ = logging.getLogger(__name__)


def load_course_data(event):
    course_uuid = event['course_uuid']
    ecosystem_uuid = event['ecosystem_uuid']

    course_values = dict(
        uuid=course_uuid,
        ecosystem_uuid=ecosystem_uuid
    )

    upsert_into(courses, course_values)
    return


def event_handler(course_uuid, event):
    event_type = event['event_type']
    __logs__.info(
        'Event handler processing event type of {}'.format(event_type))

    if event_type == 'create_course':
        load_course_data(event['event_data'])
    elif event_type == 'record_response':
        load_response(event['event_data'])

    course_event_values = dict(
        uuid=event['event_uuid'],
        sequence_number=event['sequence_number'],
        event_type=event_type,
        event_data=event['event_data'],
        course_uuid=course_uuid
    )

    upsert_into(course_events, course_event_values)

    return


def load_containers(ecosystem_uuid, contents_data):
    container_uuids = [c['container_uuid'] for c in contents_data]
    parent_uuids = [c['container_parent_uuid'] for c in
                    contents_data]
    page_modules = set(container_uuids) - set(parent_uuids)

    container_values = []
    container_exercise_values = []
    for c in contents_data:
        container_uuid = c['container_uuid']
        container = dict(
            uuid=container_uuid,
            container_parent_uuid=c['container_parent_uuid'],
            container_cnx_identity=c['container_cnx_identity'],
            ecosystem_uuid=ecosystem_uuid,
            is_page_module=container_uuid in page_modules
        )
        container_values.append(container)

        pools = c['pools']

        if pools:
            for pool in pools:
                if pool['exercise_uuids']:
                    for ex_uuid in pool['exercise_uuids']:
                        container_exercise = dict(
                            ecosystem_uuid=ecosystem_uuid,
                            container_uuid=container_uuid,
                            exercise_uuid=ex_uuid
                        )
                        container_exercise_values.append(container_exercise)
    upsert_into(container_exercises, container_exercise_values)
    upsert_into(containers, container_values)

    return


def load_ecosystem_exercises(ecosystem_uuid, exercises_data):
    eco_exercise_values = []
    for ex in exercises_data:
        eco_exercise = dict(
            ecosystem_uuid=ecosystem_uuid,
            exercise_uuid=ex['exercise_uuid']
        )
        eco_exercise_values.append(eco_exercise)

    upsert_into(ecosystem_exercises, eco_exercise_values)

    return


def load_exercises(ecosystem_uuid, exercises_data):
    __logs__.info(
        'Importing {} exercises for ecosystem {}'.format(len(exercises_data),
                                                         ecosystem_uuid))
    exercise_values = []
    for ex in exercises_data:
        exercise = dict(
            uuid=ex['exercise_uuid'],
            group_uuid=ex['group_uuid'],
            los=ex['los'],
            version=ex['version']
        )
        exercise_values.append(exercise)

    upsert_into(exercises, exercise_values)
    return


def load_ecosystem(ecosystem_uuid):
    upsert_into(ecosystems, dict(uuid=ecosystem_uuid))

    ecosystem_data = fetch_ecosystem_event_requests(ecosystem_uuid)

    contents_data = ecosystem_data['book']['contents']
    exercises_data = ecosystem_data['exercises']

    load_exercises(ecosystem_uuid, exercises_data)
    load_ecosystem_exercises(ecosystem_uuid, exercises_data)
    load_containers(ecosystem_uuid, contents_data)

    return


def load_course(course_uuid):
    cur_sequence_offset = max_sequence_offset(course_uuid)

    while True:
        cur_event_data = fetch_course_event_requests(course_uuid,
                                                     cur_sequence_offset)

        cur_events = cur_event_data['events']
        is_end = cur_event_data['is_end']

        cur_sequence_offset += len(cur_events)

        for event in cur_events:
            event_handler(course_uuid, event)

        if is_end:
            break

    return


def load_response(event_data):
    response_values = dict(course_uuid=event_data['course_uuid'],
                           ecosystem_uuid=event_data['ecosystem_uuid'],
                           exercise_uuid=event_data['exercise_uuid'],
                           is_correct=event_data['is_correct'],
                           uuid=event_data['response_uuid'],
                           student_uuid=event_data['student_uuid']
                           )
    upsert_into(responses, response_values)
    return


def run(delay_time=600):
    while True:
        # Poll for new ecosystems
        eco_uuids = fetch_pending_ecosystems(force=False)
        api_course_uuids = fetch_course_uuids()

        if eco_uuids:
            for eco_uuid in eco_uuids:
                load_ecosystem(eco_uuid)

        for course_uuid in api_course_uuids:
            load_course(course_uuid)

        delay(delay_time)
