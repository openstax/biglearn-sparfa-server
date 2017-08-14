import celery

from sparfa_server.loaders import course_loader
from sparfa_server.ddb import (
    max_sequence_offset_with_existing,
    upsert_into_do_nothing_with_existing)


@celery.task
def load_course_task(course_uuid, cur_sequence_offset = None, sequence_step_size=1):
    return course_loader(max_sequence_offset, event_handler)(*args, **kwargs)
