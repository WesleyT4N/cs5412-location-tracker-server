from http import HTTPStatus
from flask import request, jsonify, Blueprint
from marshmallow import ValidationError
from azure.cosmos import exceptions

from app.models import db, cache
from app.models.location import Location
from app.models.sensor import Sensor

from .schemas import LocationSchema, CreateLocationSchema, UpdateLocationSchema

from app.routes.sensors.utils import delete_sensor_simulation

locations_bp = Blueprint("locations", __name__, url_prefix="/api/locations")


@locations_bp.route("", methods=["GET", "POST"])
def locations():
    if request.method == "GET":
        items = Location.all()
        schema = LocationSchema(many=True, unknown="EXCLUDE")
        try:
            items = schema.load(items)
            return (
                jsonify(schema.dump(items)),
                HTTPStatus.OK,
            )
        except ValidationError as error:
            print(
                "ValidationError: Invalid format detected in location list: ",
                error.messages,
            )  # TODO: Implement logging
            return (
                "Cannot return location list. Invalid results",
                HTTPStatus.INTERNAL_SERVER_ERROR,
            )
    else:
        data = request.get_json()
        try:
            input_schema = CreateLocationSchema()
            output_schema = LocationSchema(unknown="EXCLDUE")
            new_location = input_schema.load(data)
            serialized_new_loc = output_schema.dump(new_location)
            serialized_new_loc["locationId"] = serialized_new_loc["id"]
            item = db.upsert_item(
                serialized_new_loc,
                new_location.container_name,
            )
            cache.set(Location.cache_prefix+item["id"], item)
            cache.delete("all_locations")
            item = output_schema.load(item)
            return (
                jsonify(output_schema.dump(item)),
                HTTPStatus.CREATED,
            )
        except ValidationError as error:
            # TODO: Implement logging
            print(
                "ValidationError: Could not create location: ", error.messages
            )
            return (
                "Cannot create location. Invalid arguments",
                HTTPStatus.BAD_REQUEST,
            )
        except exceptions.CosmosHttpResponseError as error:
            print("Could not create location: ", error)
            return (
                "Could not create location due to an error",
                HTTPStatus.INTERNAL_SERVER_ERROR,
            )


@locations_bp.route("/<location_id>", methods=["GET", "PUT", "DELETE"])
def location(location_id):
    if request.method == "GET":
        try:
            item = Location.get_by_id(location_id)
            schema = LocationSchema(unknown="EXCLUDE")
            item = schema.load(item)
            return (jsonify(schema.dump(item)), HTTPStatus.OK)
        except ValidationError as error:
            # TODO: Implement logging
            print("validationerror: cannot retrieve location: ", error.messages)
            return (
                "Cannot retrieve location due to schema error.",
                HTTPStatus.INTERNAL_ScERVER_ERROR,
            )
        except exceptions.CosmosResourceNotFoundError as error:
            print("Could not find location in container", error)
            return (
                "Location with id {} does not exist".format(location_id),
                HTTPStatus.NOT_FOUND,
            )
    elif request.method == "PUT":
        try:
            input_schema = UpdateLocationSchema()
            output_schema = LocationSchema(unknown="EXCLUDE")
            data = request.get_json()
            errors = input_schema.validate(data)
            if len(errors) != 0:
                raise ValidationError({"messages": errors})
            old_location = Location.get_by_id(location_id)
            merged = {
                **old_location,
                **data,
            }
            del merged["updatedAt"]
            updated_location = output_schema.load(merged)
            updated_item = db.replace_item(
                old_location,
                output_schema.dump(updated_location),
                Location.container_name,
            )
            cache.set(Location.cache_prefix+location_id, updated_item)
            cache.delete("all_locations")
            updated_item = output_schema.load(updated_item)
            return (
                jsonify(output_schema.dump(updated_item)),
                HTTPStatus.OK,
            )
        except ValidationError as error:
            print("ValidationError: Cannot update location: ",
                  error.messages)  # TODO: Implement logging
            return (
                "Cannot update location. Invalid arguments",
                HTTPStatus.BAD_REQUEST,
            )
        except exceptions.CosmosResourceNotFoundError as error:
            print("Could not find location in container", error)
            return (
                "Cannot update location that does not exist",
                HTTPStatus.NOT_FOUND,
            )
    else:  # DELETE
        try:
            item = Location.get_by_id(location_id)
            schema = LocationSchema(unknown="EXCLUDE")
            item = schema.load(item)
            sensors = item.sensors
            for sensor_id in sensors:
                sensor_id = str(sensor_id)
                delete_sensor_simulation(sensor_id, location_id)
                Sensor.delete(sensor_id, location_id)
            if Location.delete(location_id) is None:
                cache.delete(Location.cache_prefix+location_id)
                cache.delete("all_locations")
                return ("", HTTPStatus.OK)
            return (
                "Error occurred when deleting location",
                HTTPStatus.INTERNAL_SERVER_ERROR,
            )
        except ValidationError as error:
            print("ValidationError: Cannot delete location: ",
                  error.messages)  # TODO: Implement logging
            return (
                "Cannot delete location. Invalid arguments",
                HTTPStatus.BAD_REQUEST,
            )
        except exceptions.CosmosHttpResponseError as error:
            print("Could not delete location: ", error)
            return (
                "Error occurred when attempting to delete location",
                HTTPStatus.INTERNAL_SERVER_ERROR,
            )
        except exceptions.CosmosResourceNotFoundError as error:
            print("Could not find location in container", error)
            return (
                "Cannot delete location that does not exist",
                HTTPStatus.NOT_FOUND,
            )
