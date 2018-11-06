from datetime import timedelta
from functools import wraps

from celery import Celery
from celery.signals import worker_process_init
from kombu import Queue
from celery_once import QueueOnce

from ..config import AMQP_QUEUE_PREFIX, AMQP_URL, REDIS_URL
from ..orm.sessions import ENGINE
from .redis import REDIS

LOAD_ECOSYSTEM_METADATA_QUEUE = '{}load.ecosystem.metadata'.format(AMQP_QUEUE_PREFIX)
LOAD_ECOSYSTEM_EVENTS_QUEUE = '{}load.ecosystem.events'.format(AMQP_QUEUE_PREFIX)
LOAD_COURSE_METADATA_QUEUE = '{}load.course.metadata'.format(AMQP_QUEUE_PREFIX)
LOAD_COURSE_EVENTS_QUEUE = '{}load.course.events'.format(AMQP_QUEUE_PREFIX)
CALCULATE_ECOSYSTEM_MATRICES_QUEUE = '{}calculate.ecosystem-matrices'.format(AMQP_QUEUE_PREFIX)
CALCULATE_EXERCISES_QUEUE = '{}calculate.exercises'.format(AMQP_QUEUE_PREFIX)
CALCULATE_CLUES_QUEUE = '{}calculate.clues'.format(AMQP_QUEUE_PREFIX)

app = Celery('sparfa_server')
app.conf.update(
    broker_url=AMQP_URL,
    result_backend=REDIS_URL,
    result_compression='gzip',
    beat_schedule={
        'load_ecosystem_metadata': {
            'task': 'sparfa_server.tasks.loaders.load_ecosystem_metadata',
            'schedule': timedelta(seconds=1),
            'options': {'queue': LOAD_ECOSYSTEM_METADATA_QUEUE}
        },
        'load_ecosystem_events': {
            'task': 'sparfa_server.tasks.loaders.load_ecosystem_events',
            'schedule': timedelta(seconds=1),
            'options': {'queue': LOAD_ECOSYSTEM_EVENTS_QUEUE}
        },
        'load_course_metadata': {
            'task': 'sparfa_server.tasks.loaders.load_course_metadata',
            'schedule': timedelta(seconds=1),
            'options': {'queue': LOAD_COURSE_METADATA_QUEUE}
        },
        'load_course_events': {
            'task': 'sparfa_server.tasks.loaders.load_course_events',
            'schedule': timedelta(seconds=1),
            'options': {'queue': LOAD_COURSE_EVENTS_QUEUE}
        },
        'calculate_ecosystem_matrices': {
            'task': 'sparfa_server.tasks.calcs.calculate_ecosystem_matrices',
            'schedule': timedelta(seconds=1),
            'options': {'queue': CALCULATE_ECOSYSTEM_MATRICES_QUEUE}
        },
        'calculate_exercises': {
            'task': 'sparfa_server.tasks.calcs.calculate_exercises',
            'schedule': timedelta(seconds=1),
            'options': {'queue': CALCULATE_EXERCISES_QUEUE}
        },
        'calculate_clues': {
            'task': 'sparfa_server.tasks.calcs.calculate_clues',
            'schedule': timedelta(seconds=1),
            'options': {'queue': CALCULATE_CLUES_QUEUE}
        }
    },
    beat_scheduler='redbeat.schedulers.RedBeatScheduler',
    beat_max_loop_interval=1,
    redbeat_redis_url=REDIS_URL,
    redbeat_lock_timeout=5,
    accept_content=['json'],
    task_serializer='json',
    imports=('sparfa_server.tasks.loaders', 'sparfa_server.tasks.calcs'),
    task_queues=[
        Queue(LOAD_ECOSYSTEM_METADATA_QUEUE, routing_key=LOAD_ECOSYSTEM_METADATA_QUEUE),
        Queue(LOAD_ECOSYSTEM_EVENTS_QUEUE, routing_key=LOAD_ECOSYSTEM_EVENTS_QUEUE),
        Queue(LOAD_COURSE_METADATA_QUEUE, routing_key=LOAD_COURSE_METADATA_QUEUE),
        Queue(LOAD_COURSE_EVENTS_QUEUE, routing_key=LOAD_COURSE_EVENTS_QUEUE),
        Queue(CALCULATE_ECOSYSTEM_MATRICES_QUEUE, routing_key=CALCULATE_ECOSYSTEM_MATRICES_QUEUE),
        Queue(CALCULATE_EXERCISES_QUEUE, routing_key=CALCULATE_EXERCISES_QUEUE),
        Queue(CALCULATE_CLUES_QUEUE, routing_key=CALCULATE_CLUES_QUEUE)
    ],
    ONCE={
        'backend': 'celery_once.backends.Redis',
        'settings': {
            'url': REDIS_URL,
            'default_timeout': 300  # should be longer than the longest-running task
        }
    }
)


# Subprocesses cannot share file descriptors, so we explicitly reset all the connections here
@worker_process_init.connect
def reset_connections(**kwargs):
    ENGINE.dispose()
    REDIS.connection_pool.reset()


# Sets default task arguments
# All sparfa-server tasks should use this instead of using @celery.task directly
@wraps(app.task)
def task(func, **kwargs):
    defaults = {'base': QueueOnce, 'once': {'graceful': True}}
    defaults.update(kwargs)
    return app.task(func, **defaults)
