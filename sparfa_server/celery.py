from datetime import timedelta

from celery import Celery
from kombu import Queue, Exchange
from celery_once import QueueOnce

from .config import AMQP_HOST, AMQP_PORT, AMQP_USER, AMQP_PASSWORD, CELERY_APP_NAME
from .redis import REDIS_URL, redis
from .pg import engine

celery = Celery(CELERY_APP_NAME)
celery.conf.update(
    broker_url=AMQP_URL,
    task_ignore_result=True,
    result_backend=REDIS_URL,
    result_compression='gzip',
    beat_schedule={
        'load_ecosystem_metadata': {
            'task': 'sparfa_server.tasks.loaders.load_ecosystem_metadata_task',
            'schedule': timedelta(seconds=1),
            'options': {'queue' : 'load-ecosystem-metadata'}
        },
        'load_ecosystem_events': {
            'task': 'sparfa_server.tasks.loaders.load_ecosystem_events_task',
            'schedule': timedelta(seconds=1),
            'options': {'queue' : 'load-ecosystem-events'}
        },
        'load_course_metadata': {
            'task': 'sparfa_server.tasks.loaders.load_course_metadata_task',
            'schedule': timedelta(seconds=1),
            'options': {'queue' : 'load-course-metadata'}
        },
        'load_courses_events': {
            'task': 'sparfa_server.tasks.loaders.load_courses_events_task',
            'schedule': timedelta(seconds=1),
            'options': {'queue' : 'load-course-events'}
        },
        'calculate_ecosystem_matrices': {
            'task': 'sparfa_server.tasks.calcs.calculate_ecosystem_matrices_task',
            'schedule': timedelta(seconds=1),
            'options': {'queue' : 'calculate-ecosystem-matrices'}
        },
        'calculate_exercises': {
            'task': 'sparfa_server.tasks.calcs.calculate_exercises_task',
            'schedule': timedelta(seconds=1),
            'options': {'queue' : 'calculate-exercises'}
        },
        'calculate_clues': {
            'task': 'sparfa_server.tasks.calcs.calculate_clues_task',
            'schedule': timedelta(seconds=1),
            'options': {'queue' : 'calculate-clues'}
        }
    },
    accept_content=['json'],
    task_serializer='json',
    imports=(
        'sparfa_server.tasks.loaders',
        'sparfa_server.tasks.calcs'
    ),
    task_queues=[
        Queue('load-course-metadata',
              routing_key='load-course-metadata',
              exchange=Exchange('load-course-metadata', type='direct', durable=False),
              durable=False),
        Queue('load-course-events',
              routing_key='load-course-events',
              exchange=Exchange('load-course-events', type='direct', durable=False),
              durable=False),
        Queue('load-ecosystem-metadata',
              routing_key='load-ecosystem-metadata',
              exchange=Exchange('load-ecosystem-metadata', type='direct', durable=False),
              durable=False),
        Queue('load-ecosystem-events',
              routing_key='load-ecosystem-events',
              exchange=Exchange('load-ecosystem-events', type='direct', durable=False),
              durable=False),
        Queue('calculate-ecosystem-matrices',
              routing_key='calculate-ecosystem-matrices',
              exchange=Exchange('calculate-ecosystem-matrices', type='direct', durable=False),
              durable=False),
        Queue('calculate-exercises',
              routing_key='calculate-exercises',
              exchange=Exchange('calculate-exercises', type='direct', durable=False),
              durable=False),
        Queue('calculate-clues',
              routing_key='calculate-clues',
              exchange=Exchange('calculate-clues', type='direct', durable=False),
              durable=False)
    ],
    ONCE={
        'backend': 'celery_once.backends.Redis',
        'settings': {
            'url': REDIS_URL,
            'default_timeout': 60 * 60 # should be longer than the longest-running task
        }
    }
)


# Subprocesses cannot share file descriptors, so we explicitly reset all the connections here
@worker_process_init.connect
def reset_connections(**kwargs):
    engine.dispose()
    redis.connection_pool.reset()


# Sets default task arguments
# All sparfa-server tasks should use this instead of using @celery.task directly
@wraps(celery.task)
def task(*args, **kwargs):
    defaults = {'base': QueueOnce, 'once': {'graceful': True}}
    defaults.update(kwargs)
    return celery.task(*args, **defaults)
