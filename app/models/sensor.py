import json
import uuid
import datetime as dt
from .base_model import BaseModel
from .utils import DatabaseContainerEnum
from . import db

class Sensor(BaseModel):
    container_name = DatabaseContainerEnum.SENSORS.name

    def __init__(self,
        name,
        type,
        id=None,
        updated_at=None,
        location_id=None
    ):
        self.id = id
        if self.id is None:
            self.id = uuid.uuid4()
        self.name = name
        self.type = type
        self.updated_at = updated_at
        if self.updated_at is None:
            self.updated_at = dt.datetime.utcnow().replace(microsecond=0)
        self.location_id = location_id

    @staticmethod
    def get_by_id(sensor_id):
        return db.get_item_with_id(sensor_id, Sensor.container_name)

    @staticmethod
    def get_by_id_and_location_id(sensor_id, location_id):
        return db.get_item_with_id_and_partition_key(
            sensor_id,
            location_id,
            Sensor.container_name,
        )

    @staticmethod
    def all_for_location(location_id):
        query = "SELECT * FROM {} c WHERE c.locationId = '{}'".format(
            Sensor.container_name,
            location_id,
        )
        return db.query_items(Sensor.container_name, query, location_id)

    @staticmethod
    def all():
        return db.query_all_items(Sensor.container_name)

    @staticmethod
    def delete(sensor_id, location_id):
        # Does not delete ID from parent location
        return db.delete_item(sensor_id, location_id, Sensor.container_name)
