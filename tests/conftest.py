from os import environ
from re import compile, IGNORECASE

from pytest import fixture, hookimpl
from vcr import use_cassette
from vcr.errors import CannotOverwriteExistingCassetteException, UnhandledHTTPRequestError
from psycopg2 import connect
from alembic.config import Config
from alembic.command import upgrade
from unittest.mock import patch

# Force PY_ENV to be 'test' before we load our config
environ['PY_ENV'] = 'test'  # noqa

from sparfa_server.config import PY_ENV, PG_HOST, PG_PORT, PG_USER, PG_PASSWORD, PG_DB
from sparfa_server.orm import transaction as xaction
from sparfa_server.orm.sessions import Session
from sparfa_server.tasks import REDIS, app
from sparfa_server.flask import application

from constants import VCR_REQUESTS_DISABLED_REGEX

# Sanity check: abort if not in the 'test' environment so we don't ruin some non-test database
if PY_ENV != 'test':
    exit('Cannot run tests unless PY_ENV is set to "test"')


@fixture(scope='session', autouse=True)
def database():
    with connect(host=PG_HOST, port=PG_PORT, user=PG_USER,
                 password=PG_PASSWORD, dbname='postgres') as conn:
        # Drop/Create database will fail without autocommit mode
        conn.autocommit = True
        with conn.cursor() as cursor:
            # (Re)create the database
            cursor.execute('DROP DATABASE IF EXISTS {}'.format(PG_DB))
            cursor.execute('CREATE DATABASE {}'.format(PG_DB))

    # Run all migrations
    upgrade(Config('alembic.ini'), 'head')

    return PG_DB


# Make Session() return the same session object every time so we can wrap tests in transactions
# Each call to Session() will also begin a nested transaction
# so we can commit/rollback within tests and check the results
# This approach will not work for code that uses
# multiple connections to the database at the same time
@fixture(scope='session', autouse=True)
def suite_session(database):
    shared_session = Session()
    shared_session._close_suite_session = shared_session.close
    shared_session.close = shared_session.expire_all
    try:
        def nested_transaction():
            shared_session.begin_nested()
            return shared_session

        with patch('sparfa_server.orm.sessions.Session', nested_transaction):
            yield shared_session
    finally:
        shared_session._close_suite_session()


# Wrap all tests in transactions that automatically rollback
@fixture(autouse=True)
def transaction(suite_session):
    try:
        yield xaction
    finally:
        suite_session.rollback()


@fixture(autouse=True)
def redis():
    REDIS.flushdb()
    return REDIS


@fixture(autouse=True)
def celery(redis):
    app.control.purge()
    yield app


# Disable all HTTP requests unless placed inside a subclass of vcr_unittest.VCRTestCase
@fixture(scope='session', autouse=True)
def disable_http_requests():
    with use_cassette('none', record_mode='none'):
        yield


# Return a meaningful error message if we forgot to configure the tests to use VCR
@hookimpl()
def pytest_runtest_makereport(item, call):
    excinfo = call.excinfo
    if not excinfo:
        return

    if excinfo.type == CannotOverwriteExistingCassetteException:
        match = VCR_REQUESTS_DISABLED_REGEX.match(str(excinfo.value))
        if match:
            call.excinfo = excinfo.__class__((
                UnhandledHTTPRequestError,
                UnhandledHTTPRequestError(
                    "HTTP requests are currently disabled. Place tests inside a subclass of"
                    " BiglearnVCRTestCase to allow requests. Caused by: {}".format(match[1])
                ),
                excinfo.tb
            ))


@fixture(scope='session')
def flask():
    application.config['TESTING'] = True
    return application.test_client()
