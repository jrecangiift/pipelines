from cmath import log
from queue import Empty
import boto3
import json
from decimal import Decimal



class JSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return str(obj)
        return json.JSONEncoder.default(self, obj)

