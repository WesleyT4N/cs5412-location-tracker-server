from app.routes.locations.schemas import LocationSchema
from app.models.location import Location
from app.models import db, cache

from flask import current_app
import uuid
import requests
from http import HTTPStatus


def add_sensor_to_location(sensor_id, old_location):
    location_schema = LocationSchema(unknown="EXCLUDE")
    updated_location = location_schema.load(old_location)
    updated_location.sensors.append(uuid.UUID(sensor_id))
    location_id = old_location["id"]
    cache.delete(Location.cache_prefix+location_id)
    cache.delete("sensorsFor:"+location_id)
    cache.delete("all_locations")
    return db.replace_item(
        old_location,
        location_schema.dump(updated_location),
        updated_location.container_name,
    )


def remove_sensor_from_location(sensor_id, old_location):
    location_schema = LocationSchema(unknown="EXCLUDE")
    updated_location = location_schema.load(old_location)
    if uuid.UUID(sensor_id) in updated_location.sensors:
        updated_location.sensors.remove(uuid.UUID(sensor_id))
        location_id = old_location["id"]
        cache.delete(Location.cache_prefix+location_id)
        cache.delete("sensorsFor:"+location_id)
        cache.delete("all_locations")
        return db.replace_item(
            old_location,
            location_schema.dump(updated_location),
            updated_location.container_name,
        )
    return old_location


def register_sensor_simulation(sensor_id, location_id):
    url = current_app.config["SIMULATOR_SERVICE_BASE_URL"] + \
        "/api/locations/" + location_id + "/sensors/" + sensor_id
    return requests.put(url)


def delete_sensor_simulation(sensor_id, location_id):
    url = current_app.config["SIMULATOR_SERVICE_BASE_URL"] + \
        "/api/locations/" + location_id + "/sensors/" + sensor_id
    status_code = requests.delete(url).status_code
    return (status_code == HTTPStatus.OK or status_code == HTTPStatus.NOT_FOUND
            or status_code == HTTPStatus.BAD_REQUEST)
