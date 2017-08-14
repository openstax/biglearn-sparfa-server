import celery

from sparfa_server.loaders import course_loader
from sparfa_server.ddb import (
    max_sequence_offset_with_existing,
    upsert_into_do_nothing_with_existing)


def load_course_data(event):
    course_uuid = event['course_uuid']
    ecosystem_uuid = event['ecosystem_uuid']

    course_values = dict(
        uuid=course_uuid,
        ecosystem_uuid=ecosystem_uuid
    )

    upsert_into_do_nothing_with_existing(courses, course_values)
    return


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
    upsert_into_do_nothing_with_existing(responses, response_values)
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

    upsert_into_do_nothing_with_existing(course_events, course_event_values)

    return


@celery.task
def load_course_task(course_uuid, cur_sequence_offset = None, sequence_step_size=1):
    return course_loader(max_sequence_offset_with_existing, event_handler)(*args, **kwargs)
