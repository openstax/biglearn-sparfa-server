from celery import chain, group

from sparfa_server import (
    fetch_pending_ecosystems,
    fetch_course_uuids,
    fetch_ecosystem_event_requests,
    fetch_course_event_requests)
from sparfa_server.db import (
    upsert_into_do_nothing,
    max_sequence_offset)
from sparfa_server.loaders import (
    load_exercises,
    load_ecosystem_exercises,
    load_containers,
    load_course)
from sparfa_server.models import ecosystems
from sparfa_server.celery import celery

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
        results = group(load_ecosystem_task.s(ecosystem_uuid) for ecosystem_uuid in ecosystem_uuids)
        return results.apply_async(queue='beat-one')


@celery.task
def load_courses_task():
    __logs__.info('starting up load courses task')
    api_course_uuids = fetch_course_uuids()
    __logs__.info('shoulve fetched something')

    if api_course_uuids:
        results = group(load_course_task.s(course_uuid) for course_uuid in api_course_uuids)
        return results.apply_async(queue='beat-one')

