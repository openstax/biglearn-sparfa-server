from sparfa_server.tasks.redis import REDIS


def test_redis():
    assert REDIS.ping()
