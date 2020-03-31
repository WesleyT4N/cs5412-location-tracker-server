import json
import datetime as dt
import uuid

from .base_model import BaseModel
from .utils import DatabaseContainerEnum
from . import db

class Location(BaseModel):
    container_name = DatabaseContainerEnum.LOCATIONS.name

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
        return db.get_item_with_id_and_partition_key(location_id, location_id, Location.container_name)

    @staticmethod
    def all():
        return db.query_all_items(Location.container_name)

    @staticmethod
    def delete(location_id):
        return db.delete_item(location_id, location_id, Location.container_name)
