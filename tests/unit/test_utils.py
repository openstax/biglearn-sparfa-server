import os


def test_make_database_url_defaults():
    from sparfa_server.utils import make_database_url

    db_url = make_database_url()

    assert db_url == 'postgresql+psycopg2://postgres:@127.0.0.1:5432/bl_sparfa_server'


def test_make_database_url_with_env_vars():
    from sparfa_server.utils import make_database_url

    os.environ['DB_HOST'] = 'ninjaturtlefood.org'
    os.environ['DB_PORT'] = '5433'
    os.environ['DB_PASSWORD'] = 'cowabungadude'
    os.environ['DB_NAME'] = 'dominoes'
    os.environ['DB_USER'] = 'leonardo'

    db_url = make_database_url()

    assert db_url == 'postgresql+psycopg2://leonardo:cowabungadude@ninjaturtlefood.org:5433/dominoes'

