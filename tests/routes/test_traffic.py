
import pytest
import json
import uuid
import datetime as dt
import time
from http import HTTPStatus

from marshmallow import ValidationError

from tests.test_app import app
from app.routes.traffic import (
    DatastoreEndpointEnum,
    TrafficCountSchema,
    PeakTrafficSchema,
    TrafficHistorySchema,
)

class MockResponse:
    def __init__(self, enum, error=False, mock_json={}):
        self.enum = enum
        self.status_code = 200
        if error:
            self.text = "generic error"
            self.status_code = 500
        self.mock_json = mock_json

    def json(self):
        return self.mock_json


def test_can_fetch_traffic_count_for_location(app, monkeypatch):
    sensor_ids = [str(uuid.uuid4()), str(uuid.uuid4())]
    loc_id = str(uuid.uuid4())
    data_in = {
        "time": int(time.time()),
        "sensor_ids": sensor_ids,
    }

    response_json =  {
        "time": int(time.time()),
        "fetchedAt": int(time.time()),
        "trafficCount": 20,
    }

    expected_response = {
        **response_json,
        "locationId": loc_id,
    }
    def mock_get(endpoint, *args, **kwargs):
        return MockResponse(DatastoreEndpointEnum.TRAFFIC_COUNT, mock_json=response_json)

    monkeypatch.setattr("requests.get", mock_get)
    response = app.get(
        "/api/locations/{}/traffic_count".format(loc_id),
        query_string=data_in
    )
    assert response.status_code == HTTPStatus.OK
    schema = TrafficCountSchema()
    assert schema.loads(response.data) == schema.load(expected_response)


def test_can_fetch_peak_traffic_for_location(app, monkeypatch):
    sensor_ids = [str(uuid.uuid4()), str(uuid.uuid4())]
    loc_id = str(uuid.uuid4())
    data_in = {
        "start_time": int(time.time()),
        "end_time":  int(time.time()),
        "sensor_ids": sensor_ids,
    }

    response_json =  {
        "startTime": data_in["start_time"],
        "endTime": data_in["end_time"],
        "fetchedAt": int(time.time()),
        "peakTraffic": {
            "time":  int(time.time()),
            "trafficCount": 20,
        },
    }

    expected_response = {
        **response_json,
        "locationId": loc_id,
    }

    def mock_get(endpoint, *args, **kwargs):
        return MockResponse(DatastoreEndpointEnum.PEAK_TRAFFIC, mock_json=response_json)

    monkeypatch.setattr("requests.get", mock_get)
    response = app.get(
        "/api/locations/{}/peak_traffic".format(loc_id),
        query_string=data_in
    )
    assert response.status_code == HTTPStatus.OK
    schema = PeakTrafficSchema()
    assert schema.loads(response.data) == schema.load(expected_response)

def test_can_fetch_traffic_history_for_location(app, monkeypatch):
    sensor_ids = [str(uuid.uuid4()), str(uuid.uuid4())]
    loc_id = str(uuid.uuid4())
    data_in = {
        "start_time":  int(time.time()),
        "end_time":  int(time.time()),
        "sensor_ids": sensor_ids,
    }

    response_json =  {
        "startTime": data_in["start_time"],
        "endTime": data_in["end_time"],
        "fetchedAt":  int(time.time()),
        "trafficHistory": [{
            "time":  int(time.time()),
            "trafficCount": 20,
        }, {
            "time":  int(time.time()),
            "trafficCount": 5,
        }],
    }

    expected_response = {
        **response_json,
        "locationId": loc_id,
    }

    def mock_get(endpoint, *args, **kwargs):
        return MockResponse(DatastoreEndpointEnum.PEAK_TRAFFIC, mock_json=response_json)

    monkeypatch.setattr("requests.get", mock_get)
    response = app.get(
        "/api/locations/{}/traffic_history".format(loc_id),
        query_string=data_in
    )
    assert response.status_code == HTTPStatus.OK
    schema = TrafficHistorySchema()
    assert schema.loads(response.data) == schema.load(expected_response)
