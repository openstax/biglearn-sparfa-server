from os import environ


def test_make_database_url_defaults():
    db_url = make_database_url()

    assert db_url == 'postgresql://bl_sparfa_server:bl_sparfa_server@localhost:5445/bl_sparfa_server'


def test_make_database_url_with_env_vars():
    from .config import PG_URL

    environ['PG_HOST'] = 'ninjaturtlefood.org'
    environ['PG_PORT'] = '5433'
    environ['PG_PASSWORD'] = 'cowabungadude'
    environ['PG_DB'] = 'dominoes'
    environ['PG_USER'] = 'leonardo'

    db_url = make_database_url()

    assert db_url == 'postgresql://leonardo:cowabungadude@ninjaturtlefood.org:5433/dominoes'
