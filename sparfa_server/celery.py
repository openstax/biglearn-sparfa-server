import os
from datetime import timedelta

from celery import Celery
from kombu import Queue, Exchange

celery = Celery('sparfa')

def make_celery_url():
    return 'amqp://{0}:{1}@{2}:{3}'.format(
        os.environ.get('CELERY_USER', 'guest'),
        os.environ.get('CELERY_PASSWORD', 'guest'),
        os.environ.get('CELERY_HOST', '127.0.0.1'),
        os.environ.get('CELERY_PORT', '5672'),
    )

celery.conf.update(
    BROKER_URL=make_celery_url(),
    CELERY_ANNOTATIONS={
        'sparfa_server.tasks.loaders.load_courses_task':
            {
                'rate_limit': '2/h'
            }
    },
    CELERYBEAT_SCHEDULE={
        'load_ecosystems': {
            'task': 'sparfa_server.tasks.loaders.load_ecosystems_task',
            'schedule': 10
        },
        'load_courses': {
            'task': 'sparfa_server.tasks.loaders.load_courses_task',
            'schedule': timedelta(minutes=10)
        },
        'run_matrix_calc': {
            'task': 'sparfa_server.tasks.calcs.run_matrix_calc_task',
            'schedule': timedelta(minutes=10)
        },
        'run_pe_calc': {
            'task': 'sparfa_server.tasks.calcs.run_pe_calc_task',
            'schedule': timedelta(minutes=10)
        },
        'run_clue_calc': {
            'task': 'sparfa_server.tasks.calcs.run_clue_calc_task',
            'schedule': timedelta(minutes=10)
        }
    },
    CELERY_ACCEPT_CONTENT=['json'],
    CELERY_TASK_SERIALIZER='json',
    CELERY_IMPORTS=(
        'sparfa_server.tasks.loaders',
        'sparfa_server.tasks.calcs'
    ),
    CELERY_QUEUES=[
        Queue('celery',
              routing_key='celery',
              exchange=Exchange('celery', type='direct', durable=True))
    ],
    CELERYD_PREFETCH_MULTIPLIER=1,
)


def start(argv):
    celery.start(argv)
