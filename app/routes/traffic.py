from http import HTTPStatus
import datetime as dt

from flask import Blueprint, current_app, request, jsonify
from marshmallow import fields, post_load, Schema, ValidationError
from azure.cosmos import exceptions

from app.models import db
from app.models.sensor import Sensor
from app.routes.locations import get_location


traffic_bp = Blueprint("traffic", __name__, url_prefix="/api/locations/<location_id>/traffic")

class TrafficSchem(Schema):
    id = fields.UUID()
    fetched_at = fields.DateTime(data_key="fetchedAt")
    current_occupant_count = fields.Integer(data_key="currentOccupantCount")
    peak_occupant_count = fields.Integer(data_key="peakOccupantCount")

def get_current_occupant_count(sensor_ids):
    # TODO
    return 0

def get_peak_occupant_count(sensor_ids, start_time, end_time):
    # TODO
    return 0

def get_peak_traffic_time(sensor_ids, day):
    # TODO
    return dt.datetime.utcnow()

@traffic_bp.route("", methods=["GET"])
def traffic(location_id):
        location = get_location(location_id)
        if not location:
            return (
                "Cannot get traffic for location that does not exist.",
                HTTPStatus.INTERNAL_SERVER_ERROR,
            )

        sensor_ids = [
            sensor["id"]
            for sensor in Sensor.all_for_location(location_id)
        ]
