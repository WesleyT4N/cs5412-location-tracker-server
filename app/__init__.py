import os
from flask import Flask
from app.models import db

def create_app(testing=False):
    """
    Create app instance
    """
    app = Flask(__name__, instance_relative_config=True)
    app.testing = testing
    app.url_map.strict_slashes = False
    db.init_app(app)
    db.register_containers()
    register_blueprints(app)
    return app

def register_blueprints(app):
    """
    Registers app blueprints
    """
    from app.routes.locations import locations_bp
    from app.routes.sensors import sensors_bp
    app.register_blueprint(locations_bp)
    app.register_blueprint(sensors_bp)
