import pytest
import json
import uuid
import datetime as dt
from http import HTTPStatus
from marshmallow import ValidationError

from tests.test_app import app
from app.routes.locations import LocationSchema


def test_can_search_locations(app, monkeypatch):
    locs = [{
        "id": str(uuid.uuid4()),
        "name": "a test location",
        "capacity": 10,
        "sensors": [],
    }, {
        "id": str(uuid.uuid4()),
        "name": "another location",
        "capacity": 1000,
        "sensors": [],
    },]

    def mock_query_items(*args, **kwargs):
        return locs
    monkeypatch.setattr("azure.cosmos.ContainerProxy.query_items", mock_query_items)
    response = app.get("/api/locations")
    assert response.status_code == HTTPStatus.OK
    schema = LocationSchema(many=True,unknown="EXCLDUE")
    assert str(schema.load(locs)) == str(schema.loads(response.data))

def test_can_create_location(app, monkeypatch):
    new_location = {
        "name": "a test location",
        "capacity": 10,
        "sensors": [],
    }
    data_in = {
        "name": "a test location",
        "capacity": 10,
    }
    some_id = uuid.uuid4()
    def mock_upsert_item(container, item):
        item["id"] = some_id
        return item

    monkeypatch.setattr("azure.cosmos.ContainerProxy.upsert_item", mock_upsert_item)
    response = app.post(
        "/api/locations",
        data=json.dumps(data_in),
        content_type="application/json",
    )
    assert response.status_code == HTTPStatus.CREATED
    schema = LocationSchema()
    res = schema.loads(response.data, unknown="EXCLUDE")
    assert res.id == some_id
    assert res.name == new_location["name"]
    assert res.capacity == new_location["capacity"]
    assert res.sensors == new_location["sensors"]

def test_can_get_location(app, monkeypatch):
    some_id = str(uuid.uuid4())
    loc = {
        "id": some_id,
        "name": "a test location",
        "locationId": some_id,
        "capacity": 10,
        "sensors": [],
    }

    def mock_read_item(container, item_id, partition_key):
        if item_id == str(loc["id"]) and partition_key == str(loc["locationId"]):
            return loc
        return {}

    monkeypatch.setattr("azure.cosmos.ContainerProxy.read_item", mock_read_item)
    response = app.get("/api/locations/{}".format(some_id))
    assert response.status_code == HTTPStatus.OK
    schema = LocationSchema(unknown="EXCLUDE")
    loc_obj = schema.load(loc)
    res_obj = schema.loads(response.data)
    assert schema.dump(loc_obj) == schema.dump(res_obj)

def test_can_update_location(app, monkeypatch):
    some_id = str(uuid.uuid4())
    existing_loc = {
        "id": some_id,
        "name": "a test location",
        "locationId": some_id,
        "capacity": 10,
        "updatedAt": (dt.datetime.utcnow() - dt.timedelta(hours=1)).isoformat(),
        "sensors": [],
    }
    data_in = {
        "name": "a test location with updated name",
        "capacity": 20,
    }

    def mock_read_item(container, item_id, partition_key):
        if item_id == str(existing_loc["id"]) and partition_key == str(existing_loc["locationId"]):
            return existing_loc
        return {}

    def mock_replace_item(container, old_item, new_item):
        assert old_item["id"] == new_item["id"]
        return new_item

    monkeypatch.setattr("azure.cosmos.ContainerProxy.read_item", mock_read_item)
    monkeypatch.setattr("azure.cosmos.ContainerProxy.replace_item", mock_replace_item)
    response = app.put(
        "/api/locations/{}".format(some_id),
        data=json.dumps(data_in),
        content_type="application/json",
    )
    schema = LocationSchema(unknown="EXCLUDE")
    assert response.status_code == HTTPStatus.OK
    res = schema.loads(response.data)
    old = schema.load(existing_loc)
    assert res.updated_at > old.updated_at

def test_can_delete_location(app, monkeypatch):
    some_id = str(uuid.uuid4())
    existing_loc = {
        "id": some_id,
        "name": "a test location",
        "locationId": some_id,
        "capacity": 10,
        "sensors": [],
    }
    def mock_delete_item(container, item_id, partition_key):
        if item_id == existing_loc["id"]:
            return None
        return 1
    monkeypatch.setattr("azure.cosmos.ContainerProxy.delete_item", mock_delete_item)

    response = app.delete("/api/locations/{}".format(some_id))
    assert response.status_code == HTTPStatus.OK
    assert response.get_data(as_text=True) == ""
