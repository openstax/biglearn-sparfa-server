import io
import json
import os
import queue
import threading
import time
from collections import OrderedDict
from uuid import UUID

import numpy as np
from scipy.sparse import coo_matrix


from logging import getLogger

__logs__ = getLogger(__package__)


def dump_sparse_matrix(array):
    sparse_matrix = coo_matrix(array)
    return json.dumps({
        "data":     sparse_matrix.data.tolist(),
        "row":      sparse_matrix.row.tolist(),
        "col":      sparse_matrix.col.tolist(),
        "shape":    sparse_matrix.shape
    })


def load_sparse_matrix(text):
    sparse_json = json.loads(text)
    sparse_matrix = coo_matrix((sparse_json.get('data'),
                                (sparse_json.get('row'), sparse_json.get('col'))
                                ), shape = sparse_json.get('shape'))

    return sparse_matrix.toarray()


def load_mapping(text):
    d = json.loads(text)
    array = OrderedDict(sorted(d.items(), key=lambda t: t[1]))
    return array


def delay(interval):
    time.sleep(interval)

def make_database_url():
    return 'postgresql+psycopg2://{0}:{1}@{2}:{3}/{4}'.format(
        os.environ.get('DB_USER', 'postgres'),
        os.environ.get('DB_PASSWORD', ''),
        os.environ.get('DB_HOST', '127.0.0.1'),
        os.environ.get('DB_PORT', '5432'),
        os.environ.get('DB_NAME', 'bl_sparfa_server'),
    )


def validate_uuid4(uuid_string):
    try:
        val = UUID(uuid_string, version=4)
    except ValueError:
        return False

    return val.hex == uuid_string.replace('-', '')


def get_next_offset(current_offset, current_events = [], step_size=1, sequence_number_key = 'sequence_number'):
    next_offset = current_offset + step_size

    if len(current_events) is not 0:
        new_max_sequence_offset = max([current_event[sequence_number_key] for current_event in current_events])
        if new_max_sequence_offset > current_offset:
            next_offset = new_max_sequence_offset + 1

    return next_offset


def error_handler(error):
    __logs__.exception(error)


def get_try_decorator(errors=(Exception, ), on_error=error_handler):

    def try_decorator(func):

        def try_wrapped_function(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except errors as e:
                return on_error(e)

        return try_wrapped_function

    return try_decorator


try_all = get_try_decorator()


class Result(object):
    def __init__(self):
        self._evt = threading.Event()
        self._result = None

    def set_result(self, value):
        self._result = value
        self._evt.set()

    def result(self):
        self._evt.wait()
        return self._result


class WorkerPool(object):
    def __init__(self, nworker=4):
        self.nworker = nworker
        self.queue = queue.Queue()

    def start(self):
        for __ in range(self.nworker):
            threading.Thread(target=self.process_task).start()

    def add_task(self, func, *args, **kwargs):
        r = Result()
        self.queue.put((func, args, kwargs, r))
        return r

    def process_task(self):
        while True:
            func, args, kwargs, r = self.queue.get()

            r.set_result(func(*args, **kwargs))
            self.queue.task_done()
