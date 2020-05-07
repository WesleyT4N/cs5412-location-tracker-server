from http import HTTPStatus
import datetime as dt
import time
import json
from enum import Enum

from flask import Blueprint, current_app, request, jsonify
from marshmallow import fields, post_load, Schema, ValidationError
from azure.cosmos import exceptions
import requests

from app.models import db
from app.models.sensor import Sensor
from app.routes.locations import get_location

# TODO: For scaling purposes, we may want to introduce a caching layer for these traffic readings (~15 min TTL)

class DatastoreEndpointEnum(Enum):
    """
    List of possible statistics we can retrieve from the data-store
    """

    TRAFFIC_COUNT = "/traffic_count"
    PEAK_TRAFFIC = "/peak_traffic"
    TRAFFIC_HISTORY = "/traffic_history"

traffic_bp = Blueprint("traffic", __name__, url_prefix="/api/locations/<location_id>/")

class BaseTrafficSchema(Schema):
    fetched_at = fields.Int(data_key="fetchedAt", required=True)
    location_id = fields.UUID(data_key="locationId", required=True)

class TrafficCountSchema(BaseTrafficSchema):
    time = fields.Int(required=True)
    traffic_count = fields.Int(data_key="trafficCount", required=True)

class TrafficCountInputSchema(Schema):
    time = fields.Int(missing=lambda: int(time.time()), required=False)
    location_id = fields.UUID(required=False)

class PeakTrafficNestedSchema(Schema):
    time = fields.Int(required=True)
    count = fields.Int(required=True)

class PeakTrafficSchema(BaseTrafficSchema):
    peak_traffic = fields.Nested(
        PeakTrafficNestedSchema,
        data_key="peakTraffic",
        required=True,
    )

class PeakTrafficInputSchema(Schema):
    start_time = fields.Int(required=True)
    end_time = fields.Int(required=True)
    location_id = fields.UUID(required=False)

class TrafficHistorySchema(BaseTrafficSchema):
    traffic_history = fields.List(fields.Nested(
        TrafficCountSchema,
        only=("time", "traffic_count"),
    ), data_key="trafficHistory")


class TrafficHistoryInputSchema(Schema):
    start_time = fields.Int(required=True)
    end_time = fields.Int(required=True)
    location_id = fields.UUID(required=False)
    time_interval = fields.Int()

def get_sensor_ids(location_id):
    location = get_location(location_id)
    if not location:
        return None
    return [
        sensor["id"]
        for sensor in Sensor.all_for_location(location_id)
    ]

def get_from_data_store(endpoint, location_id, args):
    url = current_app.config["DATA_STORE_BASE_URL"] + "/api/locations/" + location_id + endpoint
    # Datastore expects unix timestamps rather than ISO format strings
    return requests.get(url, params=args)

@traffic_bp.route("traffic_count", methods=["GET"])
def get_traffic_count(location_id):
    input_schema = TrafficCountInputSchema()
    try:
        args = input_schema.load({
            **request.args,
            "location_id": location_id,
        })
        response = get_from_data_store(DatastoreEndpointEnum.TRAFFIC_COUNT.value, location_id, input_schema.dump(args))
        if response.status_code == HTTPStatus.OK:
            output_schema = TrafficCountSchema()
            output = output_schema.load({
                **response.json(),
                "locationId": location_id,
                "time": args["time"],
            })
            return (
                jsonify(output_schema.dump(output)),
                HTTPStatus.OK,
            )
        return (
            response.text,
            response.status_code
        )
    except ValidationError as error:
        print("ValidationError: Cannot get traffic: ", error.messages) # TODO: Implement logging
        return (
            "Cannot get traffic for requested location. Invalid request",
            HTTPStatus.BAD_REQUEST,
        )

@traffic_bp.route("peak_traffic", methods=["GET"])
def get_peak_traffic(location_id):
    input_schema = PeakTrafficInputSchema()
    try:
        args = input_schema.load({
            **request.args,
            "location_id": location_id,
        })
        response = get_from_data_store(DatastoreEndpointEnum.PEAK_TRAFFIC.value, location_id, input_schema.dump(args))
        if response.status_code == HTTPStatus.OK:
            output_schema = PeakTrafficSchema()
            output = output_schema.load({
                **response.json(), "locationId": location_id,
            })
            return (
                jsonify(output_schema.dump(output)),
                HTTPStatus.OK,
            )
        print(response.text)
        return (
            response.text,
            response.status_code
        )
    except ValidationError as error:
        print("ValidationError: Cannot get traffic: ", error.messages) # TODO: Implement logging
        return (
            "Cannot get traffic for requested location. Invalid request",
            HTTPStatus.BAD_REQUEST,
        )

@traffic_bp.route("traffic_history", methods=["GET"])
def get_traffic_history(location_id):
    input_schema = TrafficHistoryInputSchema()
    try:
        args = input_schema.load({
            **request.args,
            "location_id": location_id,
            "time_interval": 10,
        })
        response = get_from_data_store(DatastoreEndpointEnum.TRAFFIC_HISTORY.value, location_id, input_schema.dump(args))
        if response.status_code == HTTPStatus.OK:
            output_schema = TrafficHistorySchema()
            output = output_schema.load({
                **response.json(), "locationId": location_id,
            })
            return (
                jsonify(output_schema.dump(output)),
                HTTPStatus.OK,
            )
        return (
            response.text,
            response.status_code
        )
    except ValidationError as error:
        print("ValidationError: Cannot get traffic history: ", error.messages) # TODO: Implement logging
        return (
            "Cannot get traffic for requested location. Invalid request",
            HTTPStatus.BAD_REQUEST,
        )
