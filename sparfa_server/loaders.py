import logging

from sqlalchemy.exc import StatementError

from .api import (
    fetch_ecosystem_event_requests,
    fetch_course_event_requests,
    fetch_pending_ecosystems,
    fetch_course_uuids,
    fetch_pending_course_events_requests)
from .celery import celery
from .models import (
    ecosystems,
    exercises,
    ecosystem_exercises,
    container_exercises,
    containers,
    responses,
    course_events,
    courses)
from .db import max_sequence_offset, upsert_into_do_nothing
from .utils import delay, get_next_offset

__logs__ = logging.getLogger(__name__)


def load_course_data(event):
    course_uuid = event['course_uuid']
    ecosystem_uuid = event['ecosystem_uuid']

    course_values = dict(
        uuid=course_uuid,
        ecosystem_uuid=ecosystem_uuid
    )

    upsert_into_do_nothing(courses, course_values)
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

    upsert_into_do_nothing(course_events, course_event_values)

    return


@celery.task
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
    upsert_into_do_nothing(container_exercises, container_exercise_values)
    upsert_into_do_nothing(containers, container_values)

    return


@celery.task
def load_ecosystem_exercises(ecosystem_uuid, exercises_data):
    eco_exercise_values = []
    for ex in exercises_data:
        eco_exercise = dict(
            ecosystem_uuid=ecosystem_uuid,
            exercise_uuid=ex['exercise_uuid']
        )
        eco_exercise_values.append(eco_exercise)

    upsert_into_do_nothing(ecosystem_exercises, eco_exercise_values)

    return


@celery.task
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

    upsert_into_do_nothing(exercises, exercise_values)
    return


def load_ecosystem(ecosystem_uuid):
    contents_data, exercises_data = fetch_ecosystem_event_requests(ecosystem_uuid)

    try:
        upsert_into_do_nothing(ecosystems, dict(uuid=ecosystem_uuid))
    except StatementError:
        raise Exception('Are you sure that is a valid UUID?')

    load_exercises(ecosystem_uuid, exercises_data)
    load_ecosystem_exercises(ecosystem_uuid, exercises_data)
    load_containers(ecosystem_uuid, contents_data)

    return dict(success=True, msg='ecosystem_loaded_sucessfully')


def handle_course(cur_event_data, sequence_step_size=1):
    cur_events = cur_event_data['events']
    sequence_offset = cur_events[0]['sequence_number'] if len(cur_events) > 0 else 0
    course_uuid = cur_event_data['course_uuid']
    is_end = cur_event_data['is_end']
    is_gap = cur_event_data['is_gap']

    __logs__.debug('Fetchings course events for {} '
        'with {} offset '
        '{} number of events returned '
        'where is_end = {} and is_gap = {}'.format(
        course_uuid, sequence_offset, len(cur_events), is_end, is_gap
    ))

    for event in cur_events:
        event_handler(course_uuid, event)

    if is_end or is_gap:
        return None

    cur_sequence_offset = get_next_offset(sequence_offset, cur_events, sequence_step_size)

    return cur_sequence_offset


def load_course(course_uuid, cur_sequence_offset = None, sequence_step_size=1):

    if cur_sequence_offset is None:
        cur_sequence_offset = max_sequence_offset(course_uuid)

    while True:
        cur_event_data = fetch_course_event_requests(course_uuid,
                                                     cur_sequence_offset)

        cur_sequence_offset = handle_course(cur_event_data,
                                            sequence_step_size=sequence_step_size)

        if cur_sequence_offset is None:
            break

    return


def load_courses(course_event_requests):
    course_events = fetch_pending_course_events_requests(course_event_requests)

    next_sequence_offsets = [handle_course(course_event) for course_event in course_events]

    next_course_event_requests = [{
            'course_uuid': course_events[course_index]['course_uuid'],
            'sequence_offset': offset
        }  for course_index, offset in enumerate(next_sequence_offsets) if offset is not None]

    return next_course_event_requests


def load_response(event_data):
    response_values = dict(course_uuid=event_data['course_uuid'],
                           ecosystem_uuid=event_data['ecosystem_uuid'],
                           exercise_uuid=event_data['exercise_uuid'],
                           is_correct=event_data['is_correct'],
                           uuid=event_data['response_uuid'],
                           student_uuid=event_data['student_uuid'],
                           is_real_response=event_data.get('is_real_response', True),
                           responded_at=event_data['responded_at'],
                           sequence_number=event_data['sequence_number'],
                           trial_uuid=event_data['trial_uuid'],
                           )
    upsert_into_do_nothing(responses, response_values)
    return


def run(delay_time=600):
    try:
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
    except (KeyboardInterrupt, SystemExit):
        pass
