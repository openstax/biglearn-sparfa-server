import os
from datetime import timedelta

from celery import Celery
from celery_once import QueueOnce
from kombu import Queue, Exchange

from sparfa_server.utils import make_database_url

celery = Celery(os.environ.get('CELERY_APP_NAME', 'sparfa'))

def make_celery_url():
    return 'amqp://{0}:{1}@{2}:{3}'.format(
        os.environ.get('CELERY_USER', 'guest'),
        os.environ.get('CELERY_PASSWORD', 'guest'),
        os.environ.get('CELERY_HOST', '127.0.0.1'),
        os.environ.get('CELERY_PORT', '5672'),
    )

celery.conf.update(
    broker_url=make_celery_url(),
    task_ignore_result=True,
    result_backend='db+' + make_database_url(),
    result_compression='gzip',
    beat_schedule={
        'load_ecosystems': {
            'task': 'sparfa_server.tasks.loaders.load_ecosystems_task',
            'schedule': timedelta(seconds=2),
            'options': {'queue' : 'load-ecosystems'}
        },
        'load_courses_metadata': {
            'task': 'sparfa_server.tasks.loaders.load_courses_metadata_task',
            'schedule': timedelta(seconds=2),
            'options': {'queue' : 'load-courses'}
        },
        'load_courses_updates': {
            'task': 'sparfa_server.tasks.loaders.load_courses_updates_task',
            'schedule': timedelta(seconds=3),
            'options': {'queue' : 'load-courses'}
        },
        'run_matrix_calc': {
            'task': 'sparfa_server.tasks.calcs.run_matrix_calcs_task',
            'schedule': timedelta(seconds=2),
            'options': {'queue' : 'calculate-matrices'}
        },
        'run_pe_calc': {
            'task': 'sparfa_server.tasks.calcs.run_pe_calcs_task',
            'schedule': timedelta(seconds=2),
            'options': {'queue' : 'calculate-exercises'}
        },
        'run_clue_calc': {
            'task': 'sparfa_server.tasks.calcs.run_clue_calcs_task',
            'schedule': timedelta(seconds=2),
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
        Queue('celery',
              routing_key='celery',
              exchange=Exchange('celery', type='direct', durable=True)),
        Queue('load-courses',
              routing_key='load-courses',
              exchange=Exchange('load-courses', type='direct', durable=True)),
        Queue('load-ecosystems',
              routing_key='load-ecosystems',
              exchange=Exchange('load-ecosystems', type='direct', durable=True)),
        Queue('calculate-clues',
              routing_key='calculate-clues',
              exchange=Exchange('calculate-clues', type='direct', durable=True)),
        Queue('calculate-exercises',
              routing_key='calculate-exercises',
              exchange=Exchange('calculate-exercises', type='direct', durable=True)),
        Queue('calculate-matrices',
              routing_key='calculate-matrices',
              exchange=Exchange('calculate-matrices', type='direct', durable=True))
    ],
    ONCE={
        'backend': 'celery_once.backends.Redis',
        'settings': {
            'url': 'redis://localhost:6379/0',
            'default_timeout': 60 * 60 # Should be longer than the longest-running task
        }
    }
)


def task(*args, **kwargs):
    defaults = {'base': QueueOnce, 'once': {'graceful': True}}
    defaults.update(kwargs)
    return celery.task(*args, **defaults)


def start(argv):
    celery.start(argv)
