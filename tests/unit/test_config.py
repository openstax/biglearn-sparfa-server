from sys import modules
from importlib import reload

from sparfa_server import config


def test_works_without_dotenv():
    dotenv = modules['dotenv']
    modules['dotenv'] = None
    try:
        reload(config)
        assert config.PY_ENV == 'test'
    finally:
        modules['dotenv'] = dotenv
        reload(config)


def test_environment_variable_overrides():
    assert config.PY_ENV == 'test'
    assert config.PG_DB.startswith('test_')
    assert config.REDIS_DB == '13'
    assert config.AMQP_QUEUE_PREFIX == 'test.'
    assert config.BIGLEARN_SCHED_ALGORITHM_NAME == 'biglearn_sparfa_test'

    assert '/test_' in config.PG_URL
    assert config.REDIS_URL.endswith('/13')
