from http import HTTPStatus

from flask import request, jsonify, Blueprint
from marshmallow import ValidationError

from app.models import cache

from .schemas import (
    TrafficCountInputSchema,
    TrafficCountSchema,
    PeakTrafficInputSchema,
    PeakTrafficSchema,
    TrafficHistorySchema,
    TrafficHistoryInputSchema,
)
from .utils import DatastoreEndpointEnum, get_from_data_store

traffic_bp = Blueprint("traffic", __name__,
                       url_prefix="/api/locations/<location_id>/")


@traffic_bp.route("traffic_count", methods=["GET"])
@cache.cached(timeout=60)
def get_traffic_count(location_id):
    input_schema = TrafficCountInputSchema()
    try:
        args = input_schema.load({
            **request.args,
            "location_id": location_id,
        })
        response = get_from_data_store(
            DatastoreEndpointEnum.TRAFFIC_COUNT.value,
            location_id,
            input_schema.dump(args),
        )
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
        print("ValidationError: Cannot get traffic: ",
              error.messages)  # TODO: Implement logging
        return (
            "Cannot get traffic for requested location. Invalid request",
            HTTPStatus.BAD_REQUEST,
        )


@traffic_bp.route("peak_traffic", methods=["GET"])
@cache.cached(timeout=60)
def get_peak_traffic(location_id):
    input_schema = PeakTrafficInputSchema()
    try:
        args = input_schema.load({
            **request.args,
            "location_id": location_id,
        })
        response = get_from_data_store(
            DatastoreEndpointEnum.PEAK_TRAFFIC.value,
            location_id,
            input_schema.dump(args),
        )
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
        print("ValidationError: Cannot get traffic: ",
              error.messages)  # TODO: Implement logging
        return (
            "Cannot get traffic for requested location. Invalid request",
            HTTPStatus.BAD_REQUEST,
        )


@traffic_bp.route("traffic_history", methods=["GET"])
@cache.cached(timeout=60)
def get_traffic_history(location_id):
    input_schema = TrafficHistoryInputSchema()
    try:
        args = input_schema.load({
            **request.args,
            "location_id": location_id,
            "time_interval": 10,
        })
        response = get_from_data_store(
            DatastoreEndpointEnum.TRAFFIC_HISTORY.value,
            location_id,
            input_schema.dump(args),
        )
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
        print("ValidationError: Cannot get traffic history: ",
              error.messages)  # TODO: Implement logging
        return (
            "Cannot get traffic for requested location. Invalid request",
            HTTPStatus.BAD_REQUEST,
        )
