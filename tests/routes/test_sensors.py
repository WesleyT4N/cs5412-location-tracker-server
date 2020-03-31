import pytest
import json
import uuid
from http import HTTPStatus

from marshmallow import ValidationError

from tests.test_app import app
from app.routes.sensors import SensorSchema

def test_can_create_sensor(app, monkeypatch):
    some_id = str(uuid.uuid4())
    existing_loc = {
        "id": some_id,
        "name": "a test location",
        "locationId": some_id,
        "capacity": 10,
        "sensors": [],
    }
    data_in = {
        "name": "a sensor name",
        "type": "some type",
        "locationId": existing_loc["id"],
    }

    def mock_read_item(container, item_id, partition_key):
        if item_id == str(existing_loc["id"]) and partition_key == str(existing_loc["locationId"]):
            return existing_loc
        return {}

    def mock_upsert_item(container, item):
        return item

    def mock_replace_item(container, old_item, new_item):
        assert old_item["id"] == new_item["id"]
        assert len(new_item["sensors"]) == 1
        return new_item

    monkeypatch.setattr("azure.cosmos.ContainerProxy.read_item", mock_read_item)
    monkeypatch.setattr("azure.cosmos.ContainerProxy.replace_item", mock_replace_item)
    monkeypatch.setattr("azure.cosmos.ContainerProxy.upsert_item", mock_upsert_item)
    response = app.post(
        "/api/locations/{}/sensors".format(existing_loc["id"]),
        data=json.dumps(data_in),
        content_type="application/json",
    )
    assert response.status_code == HTTPStatus.CREATED
    schema = SensorSchema()
    res = schema.loads(response.data, unknown="EXCLUDE")
    assert res.id is not None and isinstance(res.id, uuid.UUID)
    assert res.name == data_in["name"]
    assert res.type == data_in["type"]
    assert str(res.location_id) == data_in["locationId"]

def test_can_search_for_sensors(app, monkeypatch):
    loc_id = str(uuid.uuid4())
    existing_sensors = [{
        "id": str(uuid.uuid4()),
        "name": "a sensor name",
        "type": "some type",
        "locationId": loc_id,
    }, {
        "id": str(uuid.uuid4()),
        "name": "a sensor name 2",
        "type": "some type 2",
        "locationId": loc_id,
    }]

    def mock_query_items(*args, **kwargs):
        return existing_sensors
    monkeypatch.setattr("azure.cosmos.ContainerProxy.query_items", mock_query_items)
    response = app.get("/api/locations/{}/sensors".format(loc_id))
    assert response.status_code == HTTPStatus.OK
    schema = SensorSchema(many=True, unknown="EXCLDUE")
    assert str(schema.load(existing_sensors)) == str(schema.loads(response.data))

def test_can_get_sensor(app, monkeypatch):
    loc_id = str(uuid.uuid4())
    existing_sensor = {
        "id": str(uuid.uuid4()),
        "name": "a sensor name",
        "type": "some type",
        "locationId": loc_id,
    }

    def mock_read_item(container, item_id, partition_key):
        if (item_id == str(existing_sensor["id"])
            and partition_key == str(existing_sensor["locationId"])
        ):
            return existing_sensor
        return {}

    monkeypatch.setattr("azure.cosmos.ContainerProxy.read_item", mock_read_item)
    response = app.get("/api/locations/{}/sensors/{}".format(loc_id, existing_sensor["id"]))
    assert response.status_code == HTTPStatus.OK
    schema = SensorSchema(unknown="EXCLDUE")
    assert str(schema.load(existing_sensor)) == str(schema.loads(response.data))

def test_can_update_sensor(app, monkeypatch):
    loc_id = str(uuid.uuid4())
    sensor_id = str(uuid.uuid4())
    existing_loc = {
        "id": loc_id,
        "name": "a test location",
        "locationId": loc_id,
        "capacity": 10,
        "sensors": [sensor_id],
    }
    existing_sensor = {
        "id": sensor_id,
        "name": "a sensor name",
        "type": "some type",
        "locationId": existing_loc["id"],
    }

    def mock_read_item(container, item_id, partition_key):
        if (
            item_id == str(existing_loc["id"])
            and partition_key == str(existing_loc["locationId"])
        ):
            return existing_loc
        if (
            item_id == str(existing_sensor["id"])
            and partition_key == str(existing_loc["locationId"])
        ):
            return existing_sensor
        return {}

    def mock_replace_item(container, old_item, new_item):
        assert old_item["id"] == new_item["id"]
        return new_item

    monkeypatch.setattr("azure.cosmos.ContainerProxy.read_item", mock_read_item)
    monkeypatch.setattr("azure.cosmos.ContainerProxy.replace_item", mock_replace_item)

    data_in = {
        "name": "an updated sensor name",
        "type": "an updated type",
    }

    expected_updated_sensor = {
        "id": existing_sensor["id"],
        "name": data_in["name"],
        "type": data_in["type"],
        "locationId": existing_loc["id"],
    }
    response = app.put(
        "/api/locations/{}/sensors/{}".format(existing_loc["id"], existing_sensor["id"]),
        data=json.dumps(data_in),
        content_type="application/json",
    )
    assert response.status_code == HTTPStatus.OK
    schema = SensorSchema(unknown="EXCLDUE")
    assert str(schema.load(expected_updated_sensor)) == str(schema.loads(response.data))

def test_can_delete_sensor(app, monkeypatch):
    loc_id = str(uuid.uuid4())
    sensor_id = str(uuid.uuid4())
    existing_loc = {
        "id": loc_id,
        "name": "a test location",
        "locationId": loc_id,
        "capacity": 10,
        "sensors": [sensor_id],
    }
    existing_sensor = {
        "id": sensor_id,
        "name": "a sensor name",
        "type": "some type",
        "locationId": existing_loc["id"],
    }

    def mock_read_item(container, item_id, partition_key):
        if (
            item_id == str(existing_loc["id"])
            and partition_key == str(existing_loc["locationId"])
        ):
            return existing_loc
        if (
            item_id == str(existing_sensor["id"])
            and partition_key == str(existing_loc["locationId"])
        ):
            return existing_sensor
        return {}

    def mock_delete_item(container, item_id, partition_key):
        if item_id == existing_sensor["id"]:
            return None
        return 1

    def mock_replace_item(container, old_item, new_item):
        assert old_item["id"] == new_item["id"]
        return new_item

    monkeypatch.setattr("azure.cosmos.ContainerProxy.read_item", mock_read_item)
    monkeypatch.setattr("azure.cosmos.ContainerProxy.replace_item", mock_replace_item)
    monkeypatch.setattr("azure.cosmos.ContainerProxy.delete_item", mock_delete_item)

    response = app.delete("/api/locations/{}/sensors/{}".format(existing_loc["id"], existing_sensor["id"]))
    assert response.status_code == HTTPStatus.OK
    assert response.get_data(as_text=True) == ""
