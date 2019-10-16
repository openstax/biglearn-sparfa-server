from functools import partial

from flask import Flask, jsonify
from werkzeug.exceptions import HTTPException, default_exceptions

from .api import blueprint

# Create and configure the app
application = Flask('BIGLEARN SPARFA SERVER', instance_relative_config=True)
application.url_map.strict_slashes = False


def jsonify_exception(code, exception):
    if hasattr(exception, 'description') and exception.description:
        payload = {'errors': [exception.description]}
    else:
        payload = {}
    response = jsonify(payload)
    if hasattr(exception, 'code') and exception.code:
        response.status_code = exception.code
    else:
        response.status_code = code
    return response


for code, exception in default_exceptions.items():
    application.errorhandler(exception)(partial(jsonify_exception, code))


application.register_blueprint(blueprint)
