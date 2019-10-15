from flask import Flask

from .api import blueprint

# Create and configure the app
application = Flask('BIGLEARN SPARFA SERVER', instance_relative_config=True)
application.register_blueprint(blueprint)
