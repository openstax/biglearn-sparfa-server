from celery import chain, group

from sparfa_server import (
    fetch_pending_ecosystems,
    fetch_course_uuids,
    fetch_ecosystem_event_requests,
    fetch_course_event_requests)
from sparfa_server.db import (
    upsert_into_do_nothing,
    max_sequence_offset,
    select_all_course_next_sequence_offsets)
from sparfa_server.loaders import (
    load_exercises,
    load_ecosystem_exercises,
    load_containers,
    load_course,
    load_courses)
from sparfa_server.models import ecosystems
from sparfa_server.celery import celery
from sparfa_server.utils import chunks

from logging import getLogger


__logs__ = getLogger(__package__)

@celery.task
def load_ecosystem_task(ecosystem_uuid):
    contents_data, exercises_data = fetch_ecosystem_event_requests(ecosystem_uuid)

    upsert_into_do_nothing(ecosystems, dict(uuid=ecosystem_uuid))

    res = chain(
        load_exercises.si(ecosystem_uuid, exercises_data),
        load_ecosystem_exercises.si(ecosystem_uuid, exercises_data),
        load_containers.si(ecosystem_uuid, contents_data))()


@celery.task
def load_course_task(*args, **kwargs):
    return load_course(*args, **kwargs)


@celery.task
def load_ecosystems_task():
    ecosystem_uuids = fetch_pending_ecosystems()

    if ecosystem_uuids:
        results = group(load_ecosystem_task.si(ecosystem_uuid) for ecosystem_uuid in ecosystem_uuids)
        return results.apply_async(queue='beat-one')


@celery.task
def load_courses_task(course_events_requests):
    if len(course_events_requests):
        __logs__.info('Loading courses')
        __logs__.info(course_events_requests)
        next_course_events_requests = load_courses(course_events_requests)
        load_courses_task.apply_async(next_course_events_requests)


@celery.task
def load_courses_latest_task():
    current_courses = select_all_course_next_sequence_offsets()

    chunked_courses = chunks(current_courses, 50)
    results = group(load_courses_task.si(course_events_requests) for course_events_requests in chunked_courses)
    return results.apply_async()

