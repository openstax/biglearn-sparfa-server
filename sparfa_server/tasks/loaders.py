from uuid import uuid4

from .celery import task
from ..api import blapi
from ..models import Ecosystem, PageExercise, Course, Response
from ..sqlalchemy import transaction


@task
def load_ecosystem_metadata():
    responses = blapi.fetch_ecosystem_metadatas()

    ecosystem_values = [{
        'uuid': response['uuid'],
        'sequence_number': 0
    } for response in responses]

    with transaction() as session:
        session.upsert(Ecosystem, ecosystem_values)


@task
def load_ecosystem_events(event_types=['create_ecosystem'], batch_size=1000):
    ecosystems = []
    with transaction() as session:
        # Group ecosystems in chunks of batch_size and send those requests at once
        for ecosystem in session.query(Ecosystem).yield_per(batch_size):
            ecosystems.append(ecosystem)
            while len(ecosystems) >= batch_size:
                ecosystems = _load_grouped_ecosystem_events(session, ecosystems)
        # Keep loading events until we completely exhaust all ecosystems
        while ecosystems:
            ecosystems = _load_grouped_ecosystem_events(session, ecosystems)


def _load_grouped_ecosystem_events(session, ecosystems):
    ecosystems_by_req_uuid = {str(uuid4()): ecosystem for ecosystem in ecosystems}
    event_requests = [{
        'ecosystem_uuid': ecosystem.uuid,
        'sequence_number_offset': ecosystem.sequence_number,
        'event_types': ['create_ecosystem'],
        'request_uuid': request_uuid
    } for request_uuid, ecosystem in ecosystems_by_req_uuid.items()]

    responses = blapi.fetch_ecosystem_events(event_requests)

    ecosystems = []
    ecosystem_values = []
    page_exercise_values = []
    for response in responses:
        events = response['events']
        ecosystem = ecosystems_by_req_uuid[response['request_uuid']]

        for event in events:
            event_type = event['event_type']
            if event_type == 'create_ecosystem':
                data = event['event_data']
                ecosystem_uuid = data['ecosystem_uuid']
                contents = data['book']['contents']
                parent_uuids = set([content['container_parent_uuid'] for content in contents])

                for content in contents:
                    container_uuid = content['container_uuid']
                    if container_uuid in parent_uuids:
                        # Ignore non-page containers (chapters, units)
                        # We only care about pages here because we only use
                        # the book_container_uuids as hints for the C matrix
                        # There are no exercises directly associated with a chapter in Tutor
                        # All exercises belong to a specific page, so they will all appear here
                        continue

                    exercise_uuids = set()
                    for pool in content['pools']:
                        for exercise_uuid in pool['exercise_uuids']:
                            exercise_uuids.add(exercise_uuid)

                    for exercise_uuid in exercise_uuids:
                        page_exercise_values.append({
                            'uuid': str(uuid4()),
                            'ecosystem_uuid': ecosystem_uuid,
                            'page_uuid': container_uuid,
                            'exercise_uuid': exercise_uuid
                        })
            else:
                raise ServerError('received unexpected event type: {}'.format(event_type))

            ecosystem.sequence_number = event['sequence_number'] + 1

        if response['is_end'] or response['is_gap']:
            if events:
                ecosystem_values.append({
                    'uuid': ecosystem.uuid,
                    'sequence_number': ecosystem.sequence_number
                })
        else:
            ecosystems.append(ecosystem)

    if page_exercise_values:
        session.upsert(PageExercise, page_exercise_values)
    if ecosystem_values:
        session.upsert(Ecosystem, ecosystem_values, conflict_update_columns=['sequence_number'])

    return ecosystems


@task
def load_course_metadata():
    responses = blapi.fetch_course_metadatas()

    course_values = [{
        'uuid': response['uuid'],
        'sequence_number': 0
    } for response in responses]

    with transaction() as session:
        session.upsert(Course, course_values)


@task
def load_course_events(event_types=['record_response'], batch_size=1000):
    courses = []
    with transaction() as session:
        # Group courses in chunks of batch_size and send those requests at once
        for course in session.query(Course).yield_per(batch_size):
            courses.append(course)
            while len(courses) >= batch_size:
                courses = _load_grouped_course_events(session, courses)
        # Keep loading events until we completely exhaust all courses
        while courses:
            courses = _load_grouped_course_events(session, courses)


def _load_grouped_course_events(session, courses):
    courses_by_req_uuid = {str(uuid4()): course for course in courses}
    event_requests = [{
        'course_uuid': course.uuid,
        'sequence_number_offset': course.sequence_number,
        'event_types': ['record_response'],
        'request_uuid': request_uuid
    } for request_uuid, course in courses_by_req_uuid.items()]

    responses = blapi.fetch_course_events(event_requests)

    courses = []
    course_values = []
    responses_dict = {}
    for response in responses:
        events = response['events']
        course = courses_by_req_uuid[response['request_uuid']]

        for event in events:
            event_type = event['event_type']
            if event_type == 'record_response':
                data = event['event_data']
                trial_uuid = data['trial_uuid']
                responses_dict[trial_uuid] = {
                    'uuid': data['response_uuid'],
                    'course_uuid': data['course_uuid'],
                    'ecosystem_uuid': data['ecosystem_uuid'],
                    'trial_uuid': trial_uuid,
                    'student_uuid': data['student_uuid'],
                    'exercise_uuid': data['exercise_uuid'],
                    'is_correct': data['is_correct'],
                    'is_real_response': data.get('is_real_response', True),
                    'responded_at': data['responded_at']
                }
            else:
                raise ServerError('received unexpected event type: {}'.format(event_type))

            course.sequence_number = event['sequence_number'] + 1

        if response['is_end'] or response['is_gap']:
            if events:
                course_values.append({
                    'uuid': course.uuid,
                    'sequence_number': course.sequence_number
                })
        else:
            courses.append(course)

    if responses_dict:
        session.upsert(Response, list(responses_dict.values()))
    if course_values:
        session.upsert(Course, course_values, conflict_update_columns=['sequence_number'])

    return courses
