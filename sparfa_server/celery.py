import os
from datetime import timedelta

from celery import Celery
from kombu import Queue, Exchange

celery = Celery(os.environ.get('CELERY_APP_NAME', 'sparfa'))

def make_celery_url():
    return 'amqp://{0}:{1}@{2}:{3}'.format(
        os.environ.get('CELERY_USER', 'guest'),
        os.environ.get('CELERY_PASSWORD', 'guest'),
        os.environ.get('CELERY_HOST', '127.0.0.1'),
        os.environ.get('CELERY_PORT', '5672'),
    )

celery.conf.update(
    BROKER_URL=make_celery_url(),
    CELERYBEAT_SCHEDULE={
        'load_ecosystems': {
            'task': 'sparfa_server.tasks.loaders.load_ecosystems_task',
            'schedule': timedelta(seconds=2),
            'options': {'queue' : 'beat-one'}
        },
        'load_courses': {
            'task': 'sparfa_server.tasks.loaders.load_courses_task',
            'schedule': timedelta(seconds=2),
            'options': {'queue' : 'beat-one'}
        },
        'run_matrix_calc': {
            'task': 'sparfa_server.tasks.calcs.run_matrix_calc_task',
            'schedule': timedelta(seconds=5),
            'options': {'queue' : 'beat-one'}
        },
        'run_pe_calc': {
            'task': 'sparfa_server.tasks.calcs.run_pe_calc_task',
            'schedule': timedelta(seconds=2),
            'options': {'queue' : 'beat-two'}
        },
        'run_clue_calc': {
            'task': 'sparfa_server.tasks.calcs.run_clue_calc_task',
            'schedule': timedelta(minutes=5),
            'options': {'queue' : 'beat-two'}
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
              exchange=Exchange('celery', type='direct', durable=True)),
        Queue('beat-one',
              routing_key='beat-one',
              exchange=Exchange('beat-one', type='direct', durable=True)),
        Queue('beat-two',
              routing_key='beat-two',
              exchange=Exchange('beat-two', type='direct', durable=True))
    ],
    CELERYD_PREFETCH_MULTIPLIER=1
)


def start(argv):
    celery.start(argv)
