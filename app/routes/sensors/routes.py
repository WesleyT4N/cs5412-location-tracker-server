from app.routes.locations.utils import get_location
from app.models.sensor import Sensor
from app.models import db, cache
from http import HTTPStatus
from flask import request, jsonify, Blueprint
from marshmallow import ValidationError
from azure.cosmos import exceptions

from .schemas import SensorSchema, CreateSensorSchema, UpdateSensorSchmea
from .utils import (add_sensor_to_location, remove_sensor_from_location,
                    delete_sensor_simulation, register_sensor_simulation)
# TODO: Add Caching Layer


sensors_bp = Blueprint("sensors", __name__,
                       url_prefix="/api/locations/<location_id>/sensors")


@sensors_bp.route("", methods=["GET", "POST"])
def sensors(location_id):
    """
    GET: Returns a list of all sensors for <location_id>
    POST: Upserts a new sensor for <location_id>
    """
    if request.method == "GET":
        location = get_location(location_id)
        if not location:
            return (
                "Cannot get sensors for location that does not exist.",
                HTTPStatus.NOT_FOUND,
            )
        items = Sensor.all_for_location(location_id)
        schema = SensorSchema(many=True, unknown="EXCLUDE")
        try:
            items = schema.load(items)
            return (jsonify(schema.dump(items)), HTTPStatus.OK)
        except ValidationError as error:
            print(
                "ValidationError: Invalid format detected in sensor list: ",
                error.messages,
            )  # TODO: Implement logging
            return (
                "Cannot return sensor list. Invalid results",
                HTTPStatus.INTERNAL_SERVER_ERROR,
            )
    else:
        location = get_location(location_id)
        if not location:
            return (
                "Cannot create sensor for location that does not exist.",
                HTTPStatus.NOT_FOUND,
            )
        data = request.get_json()
        data["locationId"] = location_id
        try:
            input_schema = CreateSensorSchema()
            output_schema = SensorSchema(unknown="EXCLUDE")
            sensor_to_be_created = input_schema.load(data)
            item = db.upsert_item(
                output_schema.dump(sensor_to_be_created),
                Sensor.container_name,
            )
            created_sensor = output_schema.load(item)
            # Side-effect: Updates location entry to contain
            # the newly created sensor id
            try:
                add_sensor_to_location(str(created_sensor.id), location)
                register_sensor_simulation(
                    str(created_sensor.id), location_id)
                return (
                    jsonify(output_schema.dump(created_sensor)),
                    HTTPStatus.CREATED
                )
                # if we failed to add, location may not exist anymore.
                # Roll back sensor creation
            except exceptions.CosmosHttpResponseError:
                Sensor.delete(str(created_sensor.id), location_id)
                return (
                    "Could not register sensor to location, does not exist.",
                    HTTPStatus.NOT_FOUND,
                )
        except ValidationError as error:
            # TODO: Implement logging
            print("ValidationError: Could not create sensor: ", error.messages)
            return (
                "Cannot create sensor. Invalid arguments",
                HTTPStatus.BAD_REQUEST,
            )
        except exceptions.CosmosHttpResponseError as error:
            print("Could not create sensor: ", error)
            return (
                "Could not create sensor due to an error",
                HTTPStatus.INTERNAL_SERVER_ERROR,
            )


@sensors_bp.route("/<sensor_id>", methods=["GET", "PUT", "DELETE"])
def sensor(location_id, sensor_id):
    if request.method == "GET":
        location = get_location(location_id)
        if not location:
            return (
                "Cannot get sensor for location that does not exist.",
                HTTPStatus.NOT_FOUND,
            )
        try:
            item = Sensor.get_by_id_and_location_id(sensor_id, location_id)
            schema = SensorSchema()
            item = schema.load(item, unknown="EXCLUDE")
            return (jsonify(schema.dump(item)), HTTPStatus.OK)
        except ValidationError as error:
            # TODO: Implement logging
            print("ValidationError: cannot retrieve sensor: ", error.messages)
            return ("cannot retrieve sensor", HTTPStatus.INTERNAL_SERVER_ERROR)
        except exceptions.CosmosResourceNotFoundError as error:
            print("Could not find sensor in container", error)
            return (
                "Location with id {} does not exist".format(location_id),
                HTTPStatus.NOT_FOUND,
            )
    elif request.method == "PUT":
        location = get_location(location_id)
        if not location:
            return (
                "Cannot update sensor for location that does not exist.",
                HTTPStatus.NOT_FOUND,
            )
        try:
            input_schema = UpdateSensorSchmea()
            data = request.get_json()
            errors = input_schema.validate(data)
            if len(errors) != 0:
                raise ValidationError(errors)
            data["locationId"] = location_id
            output_schema = SensorSchema()
            old_sensor = Sensor.get_by_id_and_location_id(
                sensor_id, location_id)
            updated_sensor = output_schema.load(data)
            updated_item = db.replace_item(
                old_sensor,
                output_schema.dump(updated_sensor),
                Sensor.container_name,
            )
            cache.delete("sensorsFor:"+location_id)
            cache.delete(Sensor.cache_prefix+sensor_id)
            cache.set(Sensor.cache_prefix+sensor_id, updated_item)
            updated_sensor = output_schema.load(
                updated_item, unknown="EXCLUDE")
            response = (jsonify(output_schema.dump(
                updated_sensor)), HTTPStatus.OK)
            return response
        except ValidationError as error:
            print("ValidationError: Cannot update sensor: ",
                  error.messages)  # TODO: Implement logging
            return (
                "Cannot update sensor. Invalid arguments",
                HTTPStatus.BAD_REQUEST,
            )
        except exceptions.CosmosResourceNotFoundError as error:
            print("Could not find sensor in container", error)
            return (
                "Cannot update sensor that does not exist",
                HTTPStatus.NOT_FOUND,
            )
    else:  # DELETE
        location = get_location(location_id)
        if not location:
            return (
                "Cannot delete sensor for location that does not exist.",
                HTTPStatus.NOT_FOUND,
            )
        try:
            if (
                remove_sensor_from_location(sensor_id, location) is not None
                and delete_sensor_simulation(sensor_id, location_id)
                and Sensor.delete(sensor_id, location_id) is None
            ):
                return ("", HTTPStatus.OK)
            return (
                "Error occurred when deleting sensor",
                HTTPStatus.INTERNAL_SERVER_ERROR,
            )
        except exceptions.CosmosHttpResponseError as error:
            print("Could not delete location: ", error)
            return (
                "Error occurred when attempting to delete location",
                HTTPStatus.INTERNAL_SERVER_ERROR,
            )
