from .utils import setup_db
from flask_caching import Cache


db = setup_db()
cache = Cache()
