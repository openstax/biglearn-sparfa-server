from flask import Flask, jsonify

from .api import ApiException, api_blueprint

# Create and configure the app
application = Flask('BIGLEARN SPARFA SERVER', instance_relative_config=True)


@application.errorhandler(ApiException)
def handle_api_exception(api_exception):
    response = jsonify(api_exception.payload)
    response.status_code = api_exception.status_code
    return response


application.register_blueprint(api_blueprint)
