from logging import getLogger, INFO

from sparfa_server.orm import *


def test_sqlalchemy_engine_logger_level():
    assert getLogger('sqlalchemy.engine').getEffectiveLevel() == INFO
