import io
import json
import os
import queue
import threading
import time
from collections import OrderedDict
from uuid import UUID

import numpy as np


def dump_matrix(array):
    memfile = io.BytesIO()
    np.save(memfile, array)
    memfile.seek(0)
    return json.dumps(memfile.read().decode('latin-1'))


def load_matrix(text):
    memfile = io.BytesIO()
    memfile.write(json.loads(text).encode('latin-1'))
    memfile.seek(0)
    return np.load(memfile)


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
