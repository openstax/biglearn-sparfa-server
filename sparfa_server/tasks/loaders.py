from celery import chain

from sparfa_server import (
    fetch_pending_ecosystems,
    fetch_course_uuids,
    fetch_ecosystem_event_requests,
    fetch_course_event_requests)
from sparfa_server.celery import celery
from sparfa_server.db import (
    upsert_into_do_nothing,
    max_sequence_offset)
from sparfa_server.loaders import (
    load_exercises,
    load_ecosystem_exercises,
    load_containers,
    event_handler)
from sparfa_server.models import ecosystems


@celery.task
def load_ecosystems_task():

    ecosystem_uuids = fetch_pending_ecosystems()

    if ecosystem_uuids:

        for ecosystem_uuid in ecosystem_uuids:
            contents_data, exercises_data = fetch_ecosystem_event_requests(ecosystem_uuid)

            upsert_into_do_nothing(ecosystems, dict(uuid=ecosystem_uuid))

            res = chain(
                load_exercises.si(ecosystem_uuid, exercises_data),
                load_ecosystem_exercises.si(ecosystem_uuid, exercises_data),
                load_containers.si(ecosystem_uuid, contents_data))()


@celery.task
def load_courses_task():
    api_course_uuids = fetch_course_uuids()

    if api_course_uuids:

        for course_uuid in api_course_uuids:
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


