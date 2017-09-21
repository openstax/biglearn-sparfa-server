from celery import chain, group

from sparfa_server import (
    fetch_pending_ecosystems,
    fetch_pending_courses_metadata,
    fetch_course_uuids,
    fetch_ecosystem_event_requests,
    fetch_course_event_requests)
from sparfa_server.db import (
    upsert_into_do_nothing,
    max_sequence_offset,
    select_all_course_next_sequence_offsets)
from sparfa_server.loaders import (
    load_ecosystem,
    load_course,
    load_course_data,
    load_courses)
from sparfa_server.models import ecosystems
from sparfa_server.celery import celery

from logging import getLogger

__logs__ = getLogger(__package__)

@celery.task
def load_ecosystem_task(ecosystem_uuid):
    return load_ecosystem(ecosystem_uuid)


@celery.task
def load_course_metadata_task(course_metadata):
    load_course_data(dict(
        course_uuid = course_metadata['uuid'],
        ecosystem_uuid = course_metadata['initial_ecosystem_uuid']
    ))


@celery.task
def load_course_task(*args, **kwargs):
    return load_course(*args, **kwargs)


@celery.task
def load_ecosystems_task():
    ecosystem_uuids = fetch_pending_ecosystems()

    if ecosystem_uuids:
        results = group(load_ecosystem_task.si(ecosystem_uuid) for ecosystem_uuid in ecosystem_uuids)
        return results.apply_async(queue='load-ecosystems')


@celery.task
def load_courses_events_task(course_events_requests):
    if len(course_events_requests):
        __logs__.debug('Loading course events')
        __logs__.debug(course_events_requests)
        next_course_events_requests = load_courses(course_events_requests)

        if len(next_course_events_requests):
            load_courses_events_task.apply_async((next_course_events_requests,), queue='load-courses')


@celery.task
def load_courses_updates_task():
    current_courses = select_all_course_next_sequence_offsets()
    chunked_courses_size = 50
    chunked_courses = [current_courses[course_index : (course_index + chunked_courses_size)]
                        for course_index in range(0, len(current_courses), chunked_courses_size)]

    results = group(load_courses_events_task.si(course_events_requests) for course_events_requests in chunked_courses)
    return results.apply_async(queue='load-courses')


@celery.task
def load_courses_metadata_task():
    pending_courses_metadata = fetch_pending_courses_metadata()

    if len(pending_courses_metadata):
        results = group(load_course_metadata_task.si(course_metadata) for course_metadata in pending_courses_metadata)
        return results.apply_async(queue='load-courses')


@celery.task
def load_courses_task():
    course_uuids = fetch_course_uuids()

    if len(course_uuids):
        results = group(load_course_task.si(course_uuid) for course_uuid in course_uuids)
        return results.apply_async()

