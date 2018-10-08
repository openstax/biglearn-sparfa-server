import io
import json
import os
import queue
import threading
import time

from functools import partial

from collections import OrderedDict
from uuid import UUID

import numpy as np
from scipy.sparse import coo_matrix

from logging import getLogger

__logs__ = getLogger(__package__)


def dump_sparse_matrix(matrix):
    sparse_matrix = coo_matrix(matrix)
    return json.dumps({
        "data":     sparse_matrix.data.tolist(),
        "row":      sparse_matrix.row.tolist(),
        "col":      sparse_matrix.col.tolist(),
        "shape":    sparse_matrix.shape
    })


def load_sparse_matrix(text):
    sparse_json = json.loads(text)
    sparse_matrix = coo_matrix(
        (sparse_json.get('data'), (sparse_json.get('row'), sparse_json.get('col'))),
        shape=sparse_json.get('shape')
    )

    return sparse_matrix.toarray()


def load_mapping(text):
    d = json.loads(text)
    array = OrderedDict(sorted(d.items(), key=lambda t: t[1]))
    return array


def validate_uuid4(uuid_string):
    try:
        val = UUID(uuid_string, version=4)
    except ValueError:
        return False

    return val.hex == uuid_string.replace('-', '')


def handle_exceptions(func, exceptions, on_exception):
    @wraps(func)
    def wrapped(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except exceptions as e:
            return on_exception(e)

    return wrapped


def log_exception(exception):
    __logs__.exception(exception)


log_exceptions = partial(handle_exceptions, (Exception,), log_exception)
