from os import environ

# General config
PY_ENV = environ.get('PY_ENV', 'development')
GITHUB_TOKEN = environ.get('GITHUB_TOKEN')
PG_HOST = environ.get('PG_HOST', 'localhost')
PG_PORT = environ.get('PG_PORT', '5445')
PG_USER = environ.get('PG_USER', 'bl_sparfa_server')
PG_PASSWORD = environ.get('PG_PASSWORD', 'bl_sparfa_server')
PG_DB = environ.get('PG_DB', 'bl_sparfa_server')
REDIS_HOST = environ.get('REDIS_HOST', 'localhost')
REDIS_PORT = environ.get('REDIS_PORT', '6336')
REDIS_PASSWORD = environ.get('REDIS_PASSWORD', '')
REDIS_DB = environ.get('REDIS_DB', '7')
AMQP_HOST = environ.get('AMQP_HOST', 'localhost')
AMQP_PORT = environ.get('AMQP_PORT', '5665')
AMQP_USER = environ.get('AMQP_USER', 'guest')
AMQP_PASSWORD = environ.get('AMQP_PASSWORD', 'guest')
CELERY_APP_NAME = environ.get('CELERY_APP_NAME', 'biglearn-sparfa-server')
BIGLEARN_API_URL = environ.get('BIGLEARN_API_URL', 'https://biglearn-api-dev.openstax.org')
BIGLEARN_API_TOKEN = environ.get('BIGLEARN_API_TOKEN')
BIGLEARN_SCHED_URL = environ.get('BIGLEARN_SCHED_URL',
                                 'https://biglearn-scheduler-dev.openstax.org')
BIGLEARN_SCHED_TOKEN = environ.get('BIGLEARN_SCHED_TOKEN')
BIGLEARN_SCHED_ALGORITHM_NAME = environ.get('BIGLEARN_SCHED_ALGORITHM_NAME', 'biglearn-sparfa')

# Environment-specific overrides
if PY_ENV == 'test':
    PG_DB = '{}_test'.format(PG_DB)
    REDIS_DB = '13'
    CELERY_APP_NAME = '{}-test'.format(CELERY_APP_NAME)

# Derived constants
PG_URL = 'postgresql://{0}:{1}@{2}:{3}/{4}'.format(PG_USER, PG_PASSWORD, PG_HOST, PG_PORT, PG_DB)
REDIS_URL = 'redis://:{0}@{1}:{2}/{3}'.format(REDIS_PASSWORD, REDIS_HOST, REDIS_PORT, REDIS_DB)
AMQP_URL = 'amqp://{0}:{1}@{2}:{3}'.format(AMQP_USER, AMQP_PASSWORD, AMQP_HOST, AMQP_PORT)
