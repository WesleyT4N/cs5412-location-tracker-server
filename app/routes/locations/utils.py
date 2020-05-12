from app.models.location import Location
from azure.cosmos import exceptions


def get_location(location_id):
    try:
        return Location.get_by_id(location_id)
    except exceptions.CosmosResourceNotFoundError as error:
        return None
