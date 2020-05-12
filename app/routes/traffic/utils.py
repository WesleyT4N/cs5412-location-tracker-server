
from app.models.sensor import Sensor
from app.routes.locations.utils import get_location
from enum import Enum
from flask import current_app
import requests


class DatastoreEndpointEnum(Enum):
    """
    List of possible statistics we can retrieve from the data-store
    """

    TRAFFIC_COUNT = "/traffic_count"
    PEAK_TRAFFIC = "/peak_traffic"
    TRAFFIC_HISTORY = "/traffic_history"


def get_sensor_ids(location_id):
    location = get_location(location_id)
    if not location:
        return None
    return [
        sensor["id"]
        for sensor in Sensor.all_for_location(location_id)
    ]


def get_from_data_store(endpoint, location_id, args):
    url = current_app.config["DATA_STORE_BASE_URL"] + \
        "/api/locations/" + location_id + endpoint
    # Datastore expects unix timestamps rather than ISO format strings
    return requests.get(url, params=args)
