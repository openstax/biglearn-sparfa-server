import os


def test_make_database_url_defaults():
    from sparfa_server.utils import make_database_url

    db_url = make_database_url()

    assert db_url == 'postgresql://bl_sparfa_server:bl_sparfa_server@localhost:5445/bl_sparfa_server'


def test_make_database_url_with_env_vars():
    from sparfa_server.utils import make_database_url

    os.environ['PG_HOST'] = 'ninjaturtlefood.org'
    os.environ['PG_PORT'] = '5433'
    os.environ['PG_PASSWORD'] = 'cowabungadude'
    os.environ['PG_DB'] = 'dominoes'
    os.environ['PG_USER'] = 'leonardo'

    db_url = make_database_url()

    assert db_url == 'postgresql://leonardo:cowabungadude@ninjaturtlefood.org:5433/dominoes'
