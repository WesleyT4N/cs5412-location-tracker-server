from marshmallow import fields, post_load, Schema
from app.models.sensor import Sensor


class SensorSchema(Schema):
    id = fields.UUID()
    name = fields.Str()
    type = fields.Str()
    updated_at = fields.DateTime(data_key="updatedAt")
    location_id = fields.UUID(data_key="locationId")

    @post_load
    def make_sensor(self, data, **kwarg):
        return Sensor(**data)


class CreateSensorSchema(Schema):
    name = fields.Str()
    type = fields.Str()
    location_id = fields.UUID(data_key="locationId")

    @post_load
    def make_sensor(self, data, **kwarg):
        return Sensor(**data)


class UpdateSensorSchmea(Schema):
    name = fields.Str()
    type = fields.Str()
