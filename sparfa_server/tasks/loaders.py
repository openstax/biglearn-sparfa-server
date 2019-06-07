from uuid import uuid4

from sqlalchemy import func

from ..biglearn import BLAPI
from ..orm import transaction, Ecosystem, EcosystemMatrix, Page, Course, Response
from .celery import task

__all__ = ('load_ecosystem_metadata', 'load_ecosystem_events',
           'load_course_metadata', 'load_course_events')


@task
def load_ecosystem_metadata(metadata_sequence_number_offset=None, batch_size=1000):
    """Load all ecosystem metadata"""
    while True:
        with transaction() as session:
            if metadata_sequence_number_offset is None:
                metadata_sequence_number_offset = session.query(
                    func.coalesce(func.max(Ecosystem.metadata_sequence_number), -1) + 1
                ).scalar()

            responses = BLAPI.fetch_ecosystem_metadatas(
                metadata_sequence_number_offset=metadata_sequence_number_offset,
                max_num_metadatas=batch_size
            )

            if responses:
                ecosystem_values = [{
                    'uuid': response['uuid'],
                    'metadata_sequence_number': response['metadata_sequence_number'],
                    'sequence_number': 0
                } for response in responses]

                session.upsert_values(Ecosystem, ecosystem_values)

            if len(responses) < batch_size:
                break


@task
def load_ecosystem_events(event_types=['create_ecosystem'], batch_size=1000):
    """Load all ecosystem events"""
    last_ecosystem_uuid = None
    ecosystem_uuids_to_requery = []
    while True:
        with transaction() as session:
            # Group ecosystems in chunks of batch_size and send those requests at once
            # This code uses the fact that ecosystems only ever receive 1 create_ecosystem event
            # to reduce the number of requests sent to biglearn-api
            query = session.query(Ecosystem)
            if last_ecosystem_uuid:
                query = query.filter(Ecosystem.uuid > last_ecosystem_uuid)
            ecosystems = query.filter(Ecosystem.sequence_number == 0).order_by(
                Ecosystem.uuid
            ).limit(batch_size).with_for_update(key_share=True, skip_locked=True).all()

            ecosystem_uuids_to_requery.extend(_load_grouped_ecosystem_events(session, ecosystems))

            if len(ecosystems) < batch_size:
                break

            last_ecosystem_uuid = ecosystems[-1].uuid

    # Retry ecosystems that we couldn't query before
    # This is done to avoid starvation, in case some ecosystem is emitting lots of events
    while ecosystem_uuids_to_requery:
        with transaction() as session:
            # Group ecosystems in chunks of batch_size and send those requests at once
            # This code uses the fact that ecosystems only ever receive 1 create_ecosystem event
            # to reduce the number of requests sent to biglearn-api
            ecosystems = session.query(Ecosystem).filter(
                Ecosystem.uuid.in_(ecosystem_uuids_to_requery[:batch_size]),
                Ecosystem.sequence_number == 0
            ).with_for_update(key_share=True, skip_locked=True).all()

            ecosystem_uuids_to_requery = ecosystem_uuids_to_requery[batch_size:]

            ecosystem_uuids_to_requery.extend(_load_grouped_ecosystem_events(session, ecosystems))


def _load_grouped_ecosystem_events(session, ecosystems):
    if not ecosystems:
        return []

    ecosystems_by_req_uuid = {str(uuid4()): ecosystem for ecosystem in ecosystems}
    event_requests = [{
        'ecosystem_uuid': ecosystem.uuid,
        'sequence_number_offset': ecosystem.sequence_number,
        'event_types': ['create_ecosystem'],
        'request_uuid': request_uuid
    } for request_uuid, ecosystem in ecosystems_by_req_uuid.items()]

    responses = BLAPI.fetch_ecosystem_events(event_requests)

    ecosystem_values = []
    page_values = []
    ecosystem_matrices = []
    ecosystem_uuids_to_requery = []
    for response in responses:
        events = response['events']
        ecosystem = ecosystems_by_req_uuid[response['request_uuid']]

        for event in events:
            event_type = event['event_type']
            if event_type == 'create_ecosystem':
                data = event['event_data']
                ecosystem_uuid = data['ecosystem_uuid']
                contents = data['book']['contents']
                parent_uuids = set(content['container_parent_uuid'] for content in contents)

                # Ignore non-page containers (chapters, units)
                # We only care about pages here because we only use
                # the book_container_uuids as hints for the C matrix
                # There are no exercises directly associated with a chapter in Tutor
                # All exercises belong to a specific page, so they will all appear here
                page_dicts = [{
                    'uuid': content['container_uuid'],
                    'ecosystem_uuid': ecosystem_uuid,
                    'exercise_uuids': set(exercise_uuid
                                          for pool in content['pools']
                                          for exercise_uuid in pool['exercise_uuids'])
                } for content in contents if content['container_uuid'] not in parent_uuids]

                page_values.extend(page_dicts)

                ecosystem_matrices.append(
                    EcosystemMatrix.from_ecosystem_uuid_pages_responses(
                        ecosystem_uuid=ecosystem_uuid,
                        pages=page_dicts,
                        responses=[]
                    )
                )

            ecosystem.sequence_number = max(ecosystem.sequence_number, event['sequence_number'] + 1)

        if events:
            ecosystem_values.append({
                'uuid': ecosystem.uuid,
                'sequence_number': ecosystem.sequence_number,
                'metadata_sequence_number': ecosystem.metadata_sequence_number
            })

        if not response['is_end'] and not response['is_gap']:
            ecosystem_uuids_to_requery.append(ecosystem.uuid)

    if page_values:
        session.upsert_values(Page, page_values)

    if ecosystem_matrices:
        session.upsert_models(EcosystemMatrix, ecosystem_matrices)

    if ecosystem_values:
        session.upsert_values(Ecosystem, ecosystem_values,
                              conflict_update_columns=['sequence_number'])

    return ecosystem_uuids_to_requery


@task
def load_course_metadata(metadata_sequence_number_offset=None, batch_size=1000):
    """Load all course metadata"""
    while True:
        with transaction() as session:
            if metadata_sequence_number_offset is None:
                metadata_sequence_number_offset = session.query(
                    func.coalesce(func.max(Course.metadata_sequence_number), -1) + 1
                ).scalar()

            responses = BLAPI.fetch_course_metadatas(
                metadata_sequence_number_offset=metadata_sequence_number_offset,
                max_num_metadatas=batch_size
            )

            if responses:
                course_values = [{
                    'uuid': response['uuid'],
                    'metadata_sequence_number': response['metadata_sequence_number'],
                    'sequence_number': 0
                } for response in responses]

                session.upsert_values(Course, course_values)

            if len(responses) < batch_size:
                break


@task
def load_course_events(event_types=['record_response'], batch_size=1000):
    """Load all course events"""
    last_course_uuid = None
    course_uuids_to_requery = []
    while True:
        with transaction() as session:
            # Group courses in chunks of batch_size and send those requests at once
            # We can't use the same shortcut used in the ecosystem_events here,
            # since there are more than 1 course_event per course
            query = session.query(Course)
            if last_course_uuid:
                query = query.filter(Course.uuid > last_course_uuid)
            courses = query.order_by(Course.uuid).limit(batch_size).with_for_update(
                key_share=True, skip_locked=True
            ).all()

            course_uuids_to_requery.extend(_load_grouped_course_events(session, courses))

            if len(courses) < batch_size:
                break

            last_course_uuid = courses[-1].uuid

    # Retry courses that we couldn't query before
    # This is done to avoid starvation, in case some course is emitting lots of events
    while course_uuids_to_requery:
        with transaction() as session:
            # Group courses in chunks of batch_size and send those requests at once
            # We can't use the same shortcut used in the ecosystem_events here,
            # since there are more than 1 course_event per course
            courses = session.query(Course).filter(
                Course.uuid.in_(course_uuids_to_requery[:batch_size])
            ).with_for_update(key_share=True, skip_locked=True).all()

            course_uuids_to_requery = course_uuids_to_requery[batch_size:]

            course_uuids_to_requery.extend(_load_grouped_course_events(session, courses))


def _load_grouped_course_events(session, courses):
    if not courses:
        return []

    courses_by_req_uuid = {str(uuid4()): course for course in courses}
    event_requests = [{
        'course_uuid': course.uuid,
        'sequence_number_offset': course.sequence_number,
        'event_types': ['record_response'],
        'request_uuid': request_uuid
    } for request_uuid, course in courses_by_req_uuid.items()]

    responses = BLAPI.fetch_course_events(event_requests)

    response_values_dict = {}
    course_values = []
    course_uuids_to_requery = []
    for response in responses:
        events = response['events']
        course = courses_by_req_uuid[response['request_uuid']]

        for event in events:
            event_type = event['event_type']
            if event_type == 'record_response':
                data = event['event_data']
                ecosystem_uuid = data['ecosystem_uuid']
                trial_uuid = data['trial_uuid']
                student_uuid = data['student_uuid']
                response_values_dict[trial_uuid] = {
                    'uuid': data['response_uuid'],
                    'course_uuid': data['course_uuid'],
                    'ecosystem_uuid': ecosystem_uuid,
                    'trial_uuid': trial_uuid,
                    'student_uuid': student_uuid,
                    'exercise_uuid': data['exercise_uuid'],
                    'is_correct': data['is_correct'],
                    'is_real_response': data.get('is_real_response', True),
                    'responded_at': data['responded_at']
                }

            course.sequence_number = max(course.sequence_number, event['sequence_number'] + 1)

        if events:
            course_values.append({
                'uuid': course.uuid,
                'sequence_number': course.sequence_number,
                'metadata_sequence_number': course.metadata_sequence_number
            })

        if not response['is_end'] and not response['is_gap']:
            course_uuids_to_requery.append(course.uuid)

    if response_values_dict:
        session.upsert_values(Response, list(response_values_dict.values()))

    if course_values:
        session.upsert_values(Course, course_values, conflict_update_columns=['sequence_number'])

    return course_uuids_to_requery
