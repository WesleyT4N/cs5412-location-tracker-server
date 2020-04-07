from http import HTTPStatus
from flask import Blueprint, current_app, request, jsonify
from marshmallow import fields, post_load, Schema, ValidationError
from azure.cosmos import exceptions

from app.models import db
from app.models.location import Location

locations_bp = Blueprint("locations", __name__, url_prefix="/api/locations")

# TODO: Add caching layer

class LocationSchema(Schema):
    id = fields.UUID()
    name = fields.Str()
    capacity = fields.Integer()
    updated_at = fields.DateTime(data_key="updatedAt")
    location_id = fields.UUID(data_key="locationId")
    sensors = fields.List(fields.UUID())

    @post_load
    def make_location(self, data, **kwarg):
        return Location(**data)

class CreateLocationSchema(Schema):
    name = fields.Str()
    capacity = fields.Integer()

    @post_load
    def make_location(self, data, **kwarg):
        return Location(**data)

class UpdateLocationSchema(Schema):
    name = fields.Str()
    capacity = fields.Integer()

def get_location(location_id):
    try:
        return Location.get_by_id(location_id)
    except exceptions.CosmosResourceNotFoundError as error:
        return None

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
                error,
            ) # TODO: Implement logging
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
            item = output_schema.load(item)
            return (
                jsonify(output_schema.dump(item)),
                HTTPStatus.CREATED,
            )
        except ValidationError as error:
            # TODO: Implement logging
            print("ValidationError: Could not create location: ", error)
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
            print("validationerror: cannot retrieve location: ", error)
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
                raise ValidationError(errors)
            data["id"] = location_id
            old_location = Location.get_by_id(location_id)
            updated_location = output_schema.load(data)
            updated_item = db.replace_item(
                old_location,
                output_schema.dump(updated_location),
                Location.container_name,
            )
            updated_item = output_schema.load(updated_item)
            return (
                jsonify(output_schema.dump(updated_item)),
                HTTPStatus.OK,
            )
        except ValidationError as error:
            print("ValidationError: Cannot update location: ", error) # TODO: Implement logging
            return (
                "Cannot update location. Invalid arguments", HTTPStatus.BAD_REQUEST,
            )
        except exceptions.CosmosResourceNotFoundError as error:
            print("Could not find location in container", error)
            return (
                "Cannot update location that does not exist",
                HTTPStatus.NOT_FOUND,
            )
    else: # DELETE
        try:
            if Location.delete(location_id) is None:
                return ("", HTTPStatus.OK)
            return (
                "Error occurred when deleting location",
                HTTPStatus.INTERNAL_SERVER_ERROR,
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
