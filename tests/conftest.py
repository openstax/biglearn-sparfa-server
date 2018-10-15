from pytest import yield_fixture
from psycopg2 import connect
from alembic.config import Config
from alembic.command import upgrade
from redis import Redis
from celery_once import backends
from click.testing import CliRunner

from ..config import PG_HOST, PG_PORT, PG_USER, PG_PASSWORD
from ..celery import celery
from ..tasks.client import BiglearnApi
from unit.helper import create_session_mock


@yield_fixture(scope='session')
def pg():
    with connect(host=PG_HOST, port=PG_PORT, user=PG_USER, password=PG_PASSWORD) as conn:
        try:
            with conn.cursor() as cursor:
                # (Re)create the database
                cursor.execute('DROP DATABASE IF EXISTS {};'.format(db))
                cursor.execute('CREATE DATABASE {};'.format(db))

            # Migrate the database
            upgrade(Config('alembic.ini'), 'head')

            yield conn
        finally:
            with conn.cursor() as cursor:
                # Ensure the database gets dropped
                cursor.execute('DROP DATABASE IF EXISTS {};'.format(db))


@yield_fixture(scope='session')
def redis():
    rr = Redis()
    rr.flushdb()
    yield rr


@yield_fixture(scope='session')
def celery(redis):
    backends.redis.redis = redis
    yield celery


@yield_fixture(scope='function')
def test_session():
    blapi = BiglearnApi(session=create_session_mock())
    yield blapi


@yield_fixture
def cli():
    runner = CliRunner()
    with runner.isolated_filesystem():
        yield runner
