# https://flask.palletsprojects.com/en/1.1.x/tutorial/factory/
from os import makedirs

from flask import Flask

from .api import blueprint

__author__ = 'OpenStax'
__copyright__ = 'Copyright 2017-18 Rice University'
__license__ = 'AGPLv3'
__version__ = '0.0.1'

__all__ = ('__author__', '__copyright__', '__license__', '__version__', 'application')

# Create and configure the app
application = Flask(__name__, instance_relative_config=True)
application.register_blueprint(blueprint)
