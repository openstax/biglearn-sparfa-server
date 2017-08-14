
import pytest
from alembic.command import upgrade
from click.testing import CliRunner

from alembic.config import Config as AlembicConfig
from pytest_postgresql.factories import (init_postgresql_database,
                                         drop_postgresql_database,
                                         get_config)
from sparfa_server.client import BiglearnApi
from unit.helper import create_session_mock


@pytest.yield_fixture(scope='session')
def config_database(request):
    connection_string = 'postgresql+psycopg2://{0}@{1}:{2}/{3}'

    config = get_config(request)
    pg_host = config.get('host')
    pg_port = config.get('port') or 5432
    pg_user = config.get('user')
    pg_db = config.get('db', 'tests')

    # Create the database
    init_postgresql_database(pg_user, pg_host, pg_port, pg_db)

    config = AlembicConfig('alembic.ini')
    upgrade(config, 'head')

    yield connection_string.format(pg_user, pg_host, pg_port, pg_db)

    # Ensure database gets dropped
    drop_postgresql_database(pg_user, pg_host, pg_port, pg_db, '9.6')


@pytest.yield_fixture(scope='session')
def db(config_database):
    from sparfa_server.executer import Executer

    executer = Executer(connection_string=config_database)

    with executer as conn:
        yield conn


@pytest.yield_fixture(scope='function')
def test_session():
    blapi = BiglearnApi(session=create_session_mock())
    yield blapi


@pytest.yield_fixture
def cli():
    runner = CliRunner()
    with runner.isolated_filesystem():
        yield runner
