from http import HTTPStatus
import datetime as dt
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

    TRAFFIC_COUNT = "/api/traffic_count"
    PEAK_TRAFFIC = "/api/peak_traffic"
    TRAFFIC_HISTORY = "/api/traffic_history"

traffic_bp = Blueprint("traffic", __name__, url_prefix="/api/locations/<location_id>/")

class BaseTrafficSchema(Schema):
    fetched_at = fields.DateTime(default=dt.datetime.utcnow(), data_key="fetchedAt", required=True)
    location_id = fields.UUID(data_key="locationId", required=True)

class TrafficCountSchema(BaseTrafficSchema):
    time = fields.DateTime(required=True)
    traffic_count = fields.Int(data_key="trafficCount", required=True)

class TrafficCountInputSchema(Schema):
    time = fields.DateTime(default=dt.datetime.utcnow(), required=False)
    sensor_ids = fields.List(fields.UUID(), required=False)
    location_id = fields.UUID(required=False)

class PeakTrafficSchema(BaseTrafficSchema):
    start_time = fields.DateTime(required=True, data_key="startTime")
    end_time = fields.DateTime(required=True, data_key="endTime")
    peak_traffic = fields.Nested(
        TrafficCountSchema,
        only=("time", "traffic_count"),
        data_key="peakTraffic",
        required=True,
    )

class PeakTrafficInputSchema(Schema):
    start_time = fields.DateTime(required=True)
    end_time = fields.DateTime(required=True)
    sensor_ids = fields.List(fields.UUID(), required=False)
    location_id = fields.UUID(required=False)

class TrafficHistorySchema(BaseTrafficSchema):
    start_time = fields.DateTime(required=True, data_key="startTime")
    end_time = fields.DateTime(required=True, data_key="endTime")
    traffic_history = fields.List(fields.Nested(
        TrafficCountSchema,
        only=("time", "traffic_count"),
    ), data_key="trafficHistory")

class TrafficHistoryInputSchema(Schema):
    start_time = fields.DateTime(required=True)
    end_time = fields.DateTime(required=True)
    sensor_ids = fields.List(fields.UUID(), required=False)
    location_id = fields.UUID(required=False)

def get_sensor_ids(location_id):
    location = get_location(location_id)
    if not location:
        return None
    return [
        sensor["id"]
        for sensor in Sensor.all_for_location(location_id)
    ]

def get_from_data_store(endpoint, args):
    url = current_app.config["DATA_STORE_BASE_URL"] + endpoint
    return requests.get(url, params=args)

@traffic_bp.route("traffic_count", methods=["GET"])
def get_traffic_count(location_id):
    input_schema = TrafficCountInputSchema()
    try:
        args = input_schema.load({
            **request.args,
            "location_id": location_id,
            "sensor_ids": request.args.getlist("sensor_ids"),
        })
        if args["sensor_ids"] is not None:
            sensor_ids = args["sensor_ids"]
        else:
            sensor_ids = get_sensor_ids(location_id)
            if sensor_ids is None:
                return (
                    "Cannot get traffic count for location that does not exist.",
                    HTTPStatus.NOT_FOUND,
                )
        if len(sensor_ids) == 0:
            return (
                "Cannot get traffic count for location that has 0 registered sensors",
                HTTPStatus.BAD_REQUEST,
            )
        response = get_from_data_store(DatastoreEndpointEnum.TRAFFIC_COUNT.value, input_schema.dump(args))
        if response.status_code == HTTPStatus.OK:
            output_schema = TrafficCountSchema()
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
            "sensor_ids": request.args.getlist("sensor_ids"),
        })
        if args["sensor_ids"] is not None:
            sensor_ids = args["sensor_ids"]
        else:
            sensor_ids = get_sensor_ids(location_id)
            if sensor_ids is None:
                return (
                    "Cannot get peak traffic for location that does not exist.",
                    HTTPStatus.NOT_FOUND,
                )
        if len(sensor_ids) == 0:
            return (
                "Cannot get peak traffic for location that has 0 registered sensors",
                HTTPStatus.BAD_REQUEST,
            )
        response = get_from_data_store(DatastoreEndpointEnum.PEAK_TRAFFIC.value, input_schema.dump(args))
        if response.status_code == HTTPStatus.OK:
            output_schema = PeakTrafficSchema()
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
            "sensor_ids": request.args.getlist("sensor_ids"),
        })
        if args["sensor_ids"] is not None:
            sensor_ids = args["sensor_ids"]
        else:
            sensor_ids = get_sensor_ids(location_id)
            if sensor_ids is None:
                return (
                    "Cannot get traffic history for location that does not exist.",
                    HTTPStatus.NOT_FOUND,
                )
        if len(sensor_ids) == 0:
            return (
                "Cannot get traffic history for location that has 0 registered sensors",
                HTTPStatus.BAD_REQUEST,
            )
        response = get_from_data_store(DatastoreEndpointEnum.TRAFFIC_HISTORY.value, input_schema.dump(args))
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
