import json
import datetime as dt
import uuid

from .base_model import BaseModel
from .utils import DatabaseContainerEnum
from . import db, cache


class Location(BaseModel):
    container_name = DatabaseContainerEnum.LOCATIONS.name
    cache_prefix = "location:"

    def __init__(self,
                 name,
                 id=None,
                 updated_at=None,
                 capacity=None,
                 location_id=None,
                 sensors=[],
                 ):
        self.id = id
        if self.id is None:
            self.id = uuid.uuid4()
        self.location_id = self.id
        self.name = name
        self.updated_at = updated_at
        if self.updated_at is None:
            self.updated_at = dt.datetime.utcnow().replace(microsecond=0)
        self.capacity = capacity
        self.sensors = sensors

    @staticmethod
    def get_by_id(location_id):
        cached_location = cache.get(Location.cache_prefix+location_id)
        if cached_location:
            return cached_location
        location = db.get_item_with_id_and_partition_key(
            location_id, location_id, Location.container_name)
        cache.set(Location.cache_prefix+location_id, location)
        return location

    @staticmethod
    @cache.cached(key_prefix="all_locations")
    def all():
        return db.query_all_items(Location.container_name)

    @staticmethod
    def delete(location_id):
        cache.delete(Location.cache_prefix+location_id)
        cache.delete("all_locations")
        return db.delete_item(location_id, location_id, Location.container_name)
