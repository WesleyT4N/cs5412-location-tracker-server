import os
from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv
from app.models import db, cache


def create_app(testing=False):
    """
    Create app instance
    """
    app = Flask(__name__, instance_relative_config=True)
    CORS(app)
    app.testing = testing
    app.url_map.strict_slashes = False
    load_env_vars(app)
    db.init_app(app)
    db.register_containers()
    register_blueprints(app)

    # FS cache
    # cache.init_app(app, {
    #     "CACHE_TYPE": "filesystem",
    #     "CACHE_THRESHOLD": 1000,
    #     "CACHE_DEFAULT_TIMEOUT": 60,
    #     "CACHE_DIR": "./cache",
    # })

    # remote cache
    cache.init_app(app, {
        "CACHE_TYPE": "app.models.cache.cache",
        "CACHE_MEMCACHED_SERVERS": [app.config["MEMCACHED_ADDR"]],
        "CACHE_MEMCACHED_USERNAME": app.config["MEMCACHED_USERNAME"],
        "CACHE_MEMCACHED_PASSWORD": app.config["MEMCACHED_PASSWORD"],
    })
    return app


def load_env_vars(app):
    dotenv_path = os.path.abspath(__file__ + "/../../.env")
    load_dotenv(dotenv_path)
    app.config["DATA_STORE_BASE_URL"] = os.environ["DATA_STORE_BASE_URL"]
    app.config["SIMULATOR_SERVICE_BASE_URL"] = os.environ["SIMULATOR_SERVICE_BASE_URL"]  # noqa
    app.config["MEMCACHED_ADDR"] = os.environ["MEMCACHED_ADDR"]
    app.config["MEMCACHED_USERNAME"] = os.environ["MEMCACHED_USERNAME"]
    app.config["MEMCACHED_PASSWORD"] = os.environ["MEMCACHED_PASSWORD"]


def register_blueprints(app):
    """
    Registers app blueprints
    """
    from app.routes.locations.routes import locations_bp
    from app.routes.sensors.routes import sensors_bp
    from app.routes.traffic.routes import traffic_bp
    app.register_blueprint(locations_bp)
    app.register_blueprint(sensors_bp)
    app.register_blueprint(traffic_bp)
