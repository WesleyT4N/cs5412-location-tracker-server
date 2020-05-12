import time
from marshmallow import fields, Schema


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
