# coding=utf-8
import json
from datetime import datetime
from decimal import Decimal

from flask import json

from sqlalchemy.ext.declarative import DeclarativeMeta

__author__ = "hanweiwei"
__date__ = "2019-06-07"


class AlchemyEncoder(json.JSONEncoder):
    # To serialize SQLalchemy objects
    def default(self, obj):
        if isinstance(obj.__class__, DeclarativeMeta):
            model_fields = {}
            for field in [x for x in dir(obj) if not x.startswith('_') and x != 'metadata']:
                data = obj.__getattribute__(field)
                try:
                    json.dumps(data)  # this will fail on non-encodable values, like other classes
                    model_fields[field] = data
                except TypeError:
                    model_fields[field] = None
            return model_fields
        if isinstance(obj, Decimal):
            return float(obj)
        if isinstance(obj, datetime):
            return obj.strftime("%Y-%m-%d %H:%M:%S")
        return json.JSONEncoder.default(self, obj)
