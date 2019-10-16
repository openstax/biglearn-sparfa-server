from flask import Flask

from .api import ApiException, api_blueprint

# Create and configure the app
application = Flask('BIGLEARN SPARFA SERVER', instance_relative_config=True)


@application.errorhandler(ApiException)
def handle_api_exception(api_exception):
    return api_exception.response


application.register_blueprint(api_blueprint)
