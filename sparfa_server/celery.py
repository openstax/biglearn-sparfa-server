import os
from datetime import timedelta

from celery import Celery
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
            'schedule': timedelta(seconds=30),
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
        Queue('beat-one',
              routing_key='beat-one',
              exchange=Exchange('beat-one', type='direct', durable=True)),
        Queue('beat-two',
              routing_key='beat-two',
              exchange=Exchange('beat-two', type='direct', durable=True))
    ],
    worker_prefetch_multiplier=0
)


def start(argv):
    celery.start(argv)
