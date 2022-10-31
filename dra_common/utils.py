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



def GetPreviousMonth(month, year):
    if month == 1:
        return [12, year-1]
    else:
        return [month-1, year]


def AddToDic(dic, key, num):
    if key in dic:
        dic[key] += num
    else:
        dic[key] = num
