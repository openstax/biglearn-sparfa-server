from unittest.mock import patch

from celery.result import AsyncResult, EagerResult
from celery_once import QueueOnce

from sparfa_server.tasks.loaders import load_ecosystem_metadata
from sparfa_server.tasks.celery import reset_connections, task


def test_celery_once(redis):
    # The first time the task is called, it is queued
    assert isinstance(load_ecosystem_metadata.delay(), AsyncResult)

    # Subsequent calls return None immediately
    for ii in range(2):
        eager_result = load_ecosystem_metadata.delay()
        assert isinstance(eager_result, EagerResult)
        assert eager_result.get() is None

    # After the lock is released, the task can be queued again
    redis.flushdb()
    assert isinstance(load_ecosystem_metadata.delay(), AsyncResult)


def test_reset_connections():
    with patch('sparfa_server.tasks.celery.ENGINE', autospec=True) as ENGINE:
        with patch(
            'sparfa_server.tasks.celery.REDIS.connection_pool', autospec=True
        ) as connection_pool:
            reset_connections()

    ENGINE.dispose.assert_called_once()
    connection_pool.reset.assert_called_once()


def test_task():
    with patch('sparfa_server.tasks.celery.app.task', autospec=True) as app_task:
        task(load_ecosystem_metadata, test=True)

    app_task.assert_called_once_with(
        load_ecosystem_metadata, base=QueueOnce, once={'graceful': True}, test=True
    )
