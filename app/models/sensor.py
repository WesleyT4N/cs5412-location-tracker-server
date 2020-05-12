import json
import uuid
import datetime as dt
from .base_model import BaseModel
from .utils import DatabaseContainerEnum
from . import db, cache


class Sensor(BaseModel):
    container_name = DatabaseContainerEnum.SENSORS.name
    cache_prefix = "sensor:"

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
        cached_sensor = cache.get(Sensor.cache_prefix+sensor_id)
        if cached_sensor:
            return cached_sensor
        sensor = db.get_item_with_id(sensor_id, Sensor.container_name)
        cache.set(Sensor.cache_prefix+sensor_id, sensor)
        return sensor

    @staticmethod
    def get_by_id_and_location_id(sensor_id, location_id):
        cached_sensor = cache.get(Sensor.cache_prefix+sensor_id)
        if cached_sensor:
            return cached_sensor
        sensor = db.get_item_with_id_and_partition_key(
            sensor_id,
            location_id,
            Sensor.container_name,
        )
        cache.set(Sensor.cache_prefix+sensor_id, sensor)
        return sensor

    @staticmethod
    def all_for_location(location_id):
        cached_sensors = cache.get("sensorsFor:"+location_id)
        if cached_sensors:
            return cached_sensors
        query = "SELECT * FROM {} c WHERE c.locationId = '{}'".format(
            Sensor.container_name,
            location_id,
        )
        sensors = db.query_items(Sensor.container_name, query, location_id)
        cache.set("sensorsFor:"+location_id, sensors)
        return sensors

    @staticmethod
    def all():
        return db.query_all_items(Sensor.container_name)

    @staticmethod
    def delete(sensor_id, location_id):
        # Does not delete ID from parent location
        cache.delete(Sensor.cache_prefix+sensor_id)
        cache.delete("sensorsFor:"+location_id)
        return db.delete_item(sensor_id, location_id, Sensor.container_name)
