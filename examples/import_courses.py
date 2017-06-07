import logging

from sparfa_server.api import (fetch_course_uuids,
                               fetch_course_event_requests)
from sparfa_server.models import (
    courses,
    get_ecosystem_by_uuid,
    upsert_and_return_id,
    upsert_into,
    course_events,
    select_by_id_or_uuid,
    ecosystems,
    exercises,
    responses,
    select_max_sequence_offset)

logging.basicConfig(level=logging.DEBUG)
__logs__ = logging.getLogger(__name__)


def import_course(event):
    course_uuid = event['course_uuid']
    ecosystem_uuid = event['ecosystem_uuid']

    course_values = dict(
        uuid=course_uuid,
        ecosystem_id=get_ecosystem_by_uuid(ecosystem_uuid).fetchone()['id']
    )

    course_id = upsert_and_return_id(courses, course_values)
    return course_id


def import_response(event_data):
    try:
        course_id = select_by_id_or_uuid(courses, **dict(
            uuid=event_data['course_uuid'])).fetchone()['id']
        ecosystem_id = select_by_id_or_uuid(ecosystems, **dict(
            uuid=event_data['ecosystem_uuid'])).fetchone()['id']
        exercise_id = select_by_id_or_uuid(exercises, **dict(
            uuid=event_data['exercise_uuid'])).fetchone()['id']
    except TypeError as e:
        raise Exception(
            'A record was not returned from the database for a response value')

    response_values = dict(course_id=course_id,
                           ecosystem_id=ecosystem_id,
                           exercise_id=exercise_id,
                           is_correct=event_data['is_correct'],
                           uuid=event_data['response_uuid'],
                           student_uuid=event_data['student_uuid']
                           )
    upsert_into(responses, response_values)
    return


def course_event_handler(course_uuid, event):
    event_type = event['event_type']
    __logs__.info(
        'Event handler processing event type of {}'.format(event_type))

    if event_type == 'create_course':
        import_course(event['event_data'])
    elif event_type == 'record_response':
        import_response(event['event_data'])

    course_event_values = dict(
        uuid=event['event_uuid'],
        sequence_number=event['sequence_number'],
        event_type=event_type,
        event_data=event['event_data'],
        course_id=select_by_id_or_uuid(courses, **dict(
            uuid=course_uuid)).fetchone()['id']
    )

    upsert_into(course_events, course_event_values)

    return


def main():
    # All course uuids from the biglearn api
    api_course_uuids = fetch_course_uuids()

    for course_uuid in api_course_uuids:
        cur_sequence_offset = select_max_sequence_offset(
            course_uuid).scalar() + 1

        if not cur_sequence_offset:
            cur_sequence_offset = 0

        while True:
            cur_event_data = fetch_course_event_requests(course_uuid,
                                                         cur_sequence_offset)

            cur_events = cur_event_data['events']
            is_end = cur_event_data['is_end']

            cur_sequence_offset += len(cur_events)

            for event in cur_events:
                course_event_handler(course_uuid, event)

            if is_end:
                break

            __logs__.debug(
                'Processing Course {} at offset {}'.format(course_uuid,
                                                           cur_sequence_offset))


if __name__ == '__main__':
    main()
