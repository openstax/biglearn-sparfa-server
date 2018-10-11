from celery.result import AsyncResult, EagerResult

from .tasks.loaders import load_ecosystems_task


class TestCelery(object):
    def test_queue_once(self, celery, redis):
        # The first time the task is called, it is queued
        assert isinstance(load_ecosystems_task.delay(), AsyncResult)

        # Subsequent calls return None immediately
        for ii in range(2):
            eager_result = load_ecosystems_task.delay()
            assert isinstance(eager_result, EagerResult)
            assert eager_result.get() is None

        redis.flushdb()
        # After the lock is released, the task can be queued again
        assert isinstance(load_ecosystems_task.delay(), AsyncResult)

        celery.control.purge()
        redis.flushdb()
