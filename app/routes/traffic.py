from http import HTTPStatus
import datetime as dt
from enum import Enum

from flask import Blueprint, current_app, request, jsonify
from marshmallow import fields, post_load, Schema, ValidationError
from azure.cosmos import exceptions
import requests

from app.models import db
from app.models.sensor import Sensor
from app.routes.locations import get_location

# TODO: For scaling purposes, we may want to introduce a caching layer for these traffic readings (~15 min TTL)

class DatastoreStatisticsEnum(Enum):
    """
    List of possible statistics we can retrieve from the data-store
    """

    TRAFFIC_COUNT = "CURRENT_TRAFFIC_COUNT"
    PEAK_TRAFFIC = "PEAK_TRAFFIC"
    TRAFFIC_HISTORY = "TRAFFIC_HISTORY"

traffic_bp = Blueprint("traffic", __name__, url_prefix="/api/locations/<location_id>/")

class BaseTrafficSchema(Schema):
    fetched_at = fields.DateTime(data_key="fetchedAt")

class TrafficCountSchema(BaseTrafficSchema):
    time = fields.DateTime()
    traffic_count = fields.Int(data_key="trafficCount")

class TrafficCountInputSchema(Schema):
    sensor_ids = fields.List(fields.UUID())


class PeakTrafficSchema(BaseTrafficSchema):
    peak_traffic = fields.Nested(
        TrafficCountSchema,
        only=("time", "traffic_count"),
        data_key="peakTrafficTime",
    )

class TrafficHistorySchema(BaseTrafficSchema):
    traffic_history = fields.List(fields.Nested(
        TrafficCountSchema,
        only=("time", "traffic_count"),
        data_key="trafficHistory",
    ))

def get_sensor_ids(location_id):
    location = get_location(location_id)
    if not location:
        return None
    return [
        sensor["id"]
        for sensor in Sensor.all_for_location(location_id)
    ]

def build_data_store_request(sensor_ids, start_time=None, end_time=None):
    pass

@traffic_bp_route("traffic_count", methods["GET"])
def get_traffic_count(location_id):
    if "sensor_ids" in request.args:
        sensor_ids = request.args.getlist("sensor_ids", None)
    else:
        sensor_ids = get_sensor_ids(location_id)
        if sensor_ids is None:
            return (
                "Cannot get traffic for location that does not exist.",
                HTTPStatus.NOT_FOUND,
            )
    if len(sensor_ids) == 0:
        return (
            "Cannot get traffic for location that has 0 registered sensors",
            HTTPStatus.BAD_REQUEST,
        )
    pass

@traffic_bp_route("peak_traffic", methods["GET"])
def get_peak_traffic(location_id):
    if "sensor_ids" in request.args:
        sensor_ids = request.args.getlist("sensor_ids", None)
    else:
        sensor_ids = get_sensor_ids(location_id)
        if sensor_ids is None:
            return (
                "Cannot get traffic for location that does not exist.",
                HTTPStatus.NOT_FOUND,
            )
    if len(sensor_ids) == 0:
        return (
            "Cannot get traffic for location that has 0 registered sensors",
            HTTPStatus.BAD_REQUEST,
        )
    pass

@traffic_bp_route("traffic_history", methods["GET"])
def get_traffic_history(location_id):
    if "sensor_ids" in request.args:
        sensor_ids = request.args.getlist("sensor_ids", None)
    else:
        sensor_ids = get_sensor_ids(location_id)
        if sensor_ids is None:
            return (
                "Cannot get traffic for location that does not exist.",
                HTTPStatus.NOT_FOUND,
            )
    if len(sensor_ids) == 0:
        return (
            "Cannot get traffic for location that has 0 registered sensors",
            HTTPStatus.BAD_REQUEST,
        )
    pass
