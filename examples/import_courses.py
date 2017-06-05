import logging

from sparfa_server.api import (fetch_course_uuids,
                               fetch_course_event_requests)
from sparfa_server.models import courses, get_ecosystem_by_uuid, \
    upsert_and_return_id, upsert_into, course_events, select_by_id_or_uuid, \
    ecosystems, exercises, responses

logging.basicConfig(level=logging.DEBUG)
__logs__ = logging.getLogger(__name__)


def summary_common(event):
    print('{:4d} {} {:30s}'.format(
        event['sequence_number'],
        event['event_uuid'],
        event['event_type'],
    ))


def summary_create_course(event):
    print(' ' * 10 + 'course {} ecosystem {}'.format(
        event['event_data']['course_uuid'],
        event['event_data']['ecosystem_uuid'],
    ))


def summary_global_exclusions(event):
    print(' ' * 10 + 'num_excls {} '.format(
        len(event['event_data']['exclusions']),
    ))


def summary_course_exclusions(event):
    print(' ' * 10 + 'num_excls {} '.format(
        len(event['event_data']['exclusions']),
    ))


def summary_update_roster(event):
    print(' ' * 10 + 'num_containers {:3d} num_students {:3d}'.format(
        len(event['event_data']['course_containers']),
        len(event['event_data']['students']),
    ))
    # print(' '*10 + '{}'.format(event['event_data'].keys()))


def summary_prepare_ecosystem(event):
    print(' ' * 10 + 'prep {} from {} to {}'.format(
        event['event_data']['preparation_uuid'],
        event['event_data']['ecosystem_map']['from_ecosystem_uuid'],
        event['event_data']['ecosystem_map']['to_ecosystem_uuid'],
    ))


def summary_update_ecosystem(event):
    print(' ' * 10 + 'prep {}'.format(
        event['event_data']['preparation_uuid'],
    ))


def summary_update_assignment(event):
    print(
        ' ' * 10 + 'assignment {} student {} type {:10s} pes? {:5s} spes? {:5s}'.format(
            event['event_data']['assignment_uuid'],
            event['event_data']['student_uuid'],
            event['event_data']['assignment_type'],
            str(event['event_data']['pes_are_assigned']),
            str(event['event_data']['spes_are_assigned']),
        ))


def summary_record_response(event):
    if 'responded_at' in event['event_data']:
        responded_at = event['event_data']['responded_at']
        print(responded_at)
    else:
        responded_at = ''

    if 'trial_uuid' in event['event_data']:
        trial_uuid = event['event_data']['trial_uuid']
    else:
        trial_uuid = ''

    if 'is_correct' in event['event_data']:
        is_correct = event['event_data']['is_correct']
        print(is_correct)
    else:
        is_correct = ''

    print(' ' * 10 + 'student {} time {} trial {} correct? {}'.format(
        event['event_data']['student_uuid'],
        responded_at,
        trial_uuid,
        is_correct,
    ))


def import_course(event):
    course_uuid = event['event_data']['course_uuid']
    ecosystem_uuid = event['event_data']['ecosystem_uuid']

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


def course_event_handler(event):
    event_type = event['event_type']
    __logs__.debug(
        'Event handler processing event type of {}'.format(event_type))

    if event_type == 'create_course':
        # summary_create_course(event)
        import_course(event)
    elif event_type == 'record_response':
        # summary_record_response(event)
        import_response(event['event_data'])

    course_event_values = dict(
        uuid=event['event_uuid'],
        sequence_number=event['sequence_number'],
        event_type=event_type,
        event_data=event['event_data']
    )

    upsert_into(course_events, course_event_values)

    return


def main():
    # All course uuids from the biglearn api
    api_course_uuids = fetch_course_uuids()

    for course_uuid in api_course_uuids:
        cur_sequence_offset = 6963
        while True:
            cur_event_data = fetch_course_event_requests(course_uuid,
                                                         cur_sequence_offset)

            cur_events = cur_event_data['events']
            is_end = cur_event_data['is_end']

            cur_sequence_offset += len(cur_events)

            for event in cur_events:
                course_event_handler(event)

            if is_end:
                break

            __logs__.debug(
                'Processing Course {} at offset {}'.format(course_uuid,
                                                           cur_sequence_offset))


if __name__ == '__main__':
    main()
