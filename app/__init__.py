import os
from flask import Flask
from dotenv import load_dotenv
from app.models import db

def create_app(testing=False):
    """
    Create app instance
    """
    app = Flask(__name__, instance_relative_config=True)
    app.testing = testing
    app.url_map.strict_slashes = False
    load_env_vars(app)
    db.init_app(app)
    db.register_containers()
    register_blueprints(app)
    return app

def load_env_vars(app):
    dotenv_path = os.path.abspath(__file__ + "/../../.env")
    load_dotenv(dotenv_path)
    app.config["DATA_STORE_BASE_URL"] = os.environ["DATA_STORE_BASE_URL"]

def register_blueprints(app):
    """
    Registers app blueprints
    """
    from app.routes.locations import locations_bp
    from app.routes.sensors import sensors_bp
    from app.routes.traffic import traffic_bp
    app.register_blueprint(locations_bp)
    app.register_blueprint(sensors_bp)
    app.register_blueprint(traffic_bp)
