from enum import Enum
import os

from azure.cosmos import CosmosClient
from dotenv import load_dotenv
from flask import current_app

QUERY_LIMIT = 100

class DatabaseContainerEnum(Enum):
    LOCATIONS = 'locations'
    SENSORS = 'sensors'

class DatabaseClient:
    """
    Barebones wrapper for Azure CosmosClient
    """
    def __init__(self, client, database_name):
        self.client = client
        self.database_client = self.client.get_database_client(database_name)
        self.containers = {}

    def register_container(self, container_name, container_id):
        self.containers[container_name] = self.database_client.get_container_client(container_id)

    def get_container(self, container_name):
        if container_name not in self.containers:
            raise ValueError("Container name: {} not found".format(container_name))
        return self.containers[container_name]

    def query_items(self, container_name, query, partition_key=None):
        # TODO: For scaling purposes, look into pagination
        items = self.get_container(container_name).query_items(
            query,
            partition_key=partition_key,
            enable_cross_partition_query=(partition_key is None),
        )
        return [item for item in items]

    def query_all_items(self, container_name):
        if container_name not in self.containers:
            raise ValueError("Container name: {} not found".format(container_name))
        container_id = self.containers[container_name].id
        items = self.containers[container_name].query_items(
            "SELECT * FROM {}".format(container_id),
            enable_cross_partition_query=True,
        )
        return [item for item in items]

    def get_item_with_id(self, item_id, container_name):
        # NOTE:INEFFICIENT DUE TO LACK OF PARTITION KEY
        if container_name not in self.containers:
            raise ValueError("Container name: {} not found".format(container_name))
        container_id = self.containers[container_name].id
        items = self.containers[container_name].query_items(
            "SELECT * FROM {} c WHERE c.id = '{}' OFFSET 0 LIMIT 1".format(container_id, item_id),
            enable_cross_partition_query=True,
        )
        return items[0] if len(items) > 0 else None

    def get_item_with_id_and_partition_key(self, item_id, partition_key, container_name):
        if container_name not in self.containers:
            raise ValueError("Container name: {} not found".format(container_name))
        return self.containers[container_name].read_item(item_id, partition_key)

    def upsert_item(self, item, container_name):
        """Upsert single item into DB. Returns the upserted item"""
        if container_name not in self.containers:
            raise ValueError("Container name: {} not found".format(container_name))
        return self.containers[container_name].upsert_item(item)

    def replace_item(self, old_item, new_item, container_name):
        if container_name not in self.containers:
            raise ValueError("Container name: {} not found".format(container_name))
        new_item["id"] = old_item["id"]
        return self.containers[container_name].replace_item(old_item, new_item)

    def delete_item(self, item_id, partition_key, container_name):
        if container_name not in self.containers:
            raise ValueError("Container name: {} not found".format(container_name))
        return self.containers[container_name].delete_item(item_id, partition_key)

    def init_app(self, app):
        self.app = app

    def register_containers(self):
        if self.app.config["TESTING"]:
            for container in DatabaseContainerEnum:
                self.register_container(container.name, container.value + "_test")
        else:
            for container in DatabaseContainerEnum:
                self.register_container(container.name, container.value)

def setup_db():
    dotenv_path = os.path.abspath(__file__ + "/../../../.env.local")
    load_dotenv(dotenv_path)
    url = os.environ["ACCOUNT_URI"]
    key = os.environ["ACCOUNT_KEY"]
    client = CosmosClient(url, credential=key)
    database_id = os.environ["DATABASE_ID"]
    db = DatabaseClient(client, database_id)
    return db
