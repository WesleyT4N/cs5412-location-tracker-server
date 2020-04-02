import json
import datetime as dt
import uuid

from .base_model import BaseModel
from .utils import DatabaseContainerEnum
from . import db

from app.models.sensor import Sensor

class Traffic(BaseModel):
    def __init__(self,
        id=None,
        fetched_at=None,
    ):
        self.id = id
        if self.id is None:
            self.id = uuid.uuid4()
        self.location_id = location_id
