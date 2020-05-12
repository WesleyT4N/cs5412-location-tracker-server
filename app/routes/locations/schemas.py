from marshmallow import fields, post_load, Schema

from app.models.location import Location
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
