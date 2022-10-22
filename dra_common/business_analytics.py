from cmath import nan
from dataclasses import dataclass
from multiprocessing.connection import Client
from unicodedata import decimal
from xmlrpc.client import Boolean
import boto3
from boto3.dynamodb.conditions import Key
import json
from decimal import Decimal
import decimal
from dataclasses import dataclass, field
from dataclasses_json import dataclass_json
from typing import Dict,List
from enum import Enum
from client_configuration_model import ClientConfiguration
from fx_conversion import FXConverter
from revenue_model import BusinessLine, RevenueItem
import pandas as pd
import client_aggregate_model as cam
import traceback


