from calendar import month
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
from revenue_model import RevenueClassification


CLIENT_CONFIG_BUCKET = 'dra-config'

@dataclass_json
@dataclass
class RedemptionMapping:
    internal_redemption: str
    redemption_option: str

@dataclass_json
@dataclass
class LBMSConfiguration:
    local_ccy: str = "USD"
    point_value_to_local_ccy: Decimal = Decimal(1)
    include_comms :Boolean = False


@dataclass_json
@dataclass
class FloatLinearRevenue:
    classification: RevenueClassification = RevenueClassification()
    alpha:Decimal = Decimal(0)
    beta:Decimal = Decimal(0)
    index:str=""
    currency_code:str = ""
    label:str = ""
    net_offset: Decimal= 0


@dataclass_json
@dataclass
class FloatMinMaxLinearRevenue:
    classification: RevenueClassification = RevenueClassification()
    alpha:Decimal = Decimal(0)
    beta:Decimal = Decimal(0)
    index:str=""
    currency_code:str = ""
    label:str = ""
    net_offset: Decimal= 0
    has_min: Boolean= False
    min: Decimal = Decimal(0)
    has_max: Boolean= False
    max: Decimal = Decimal(0)
    
@dataclass_json
@dataclass
class RecurringFixedRevenue:
    classification: RevenueClassification = RevenueClassification()
    amount:Decimal = 0
    currency_code:str = ""
    label:str = ""
    net_offset: Decimal= 0

@dataclass_json
@dataclass
class SingleFixedRevenue:
    month:int = 1
    year:int = 1990
    classification: RevenueClassification = RevenueClassification()
    amount:Decimal = 0
    currency_code:str = ""
    label:str = ""
    net_offset: Decimal= 0

@dataclass_json
@dataclass
class FloatRevenues:
    linear:List[FloatLinearRevenue] = field(default_factory=list)
    min_max_linear: List[FloatMinMaxLinearRevenue] = field(default_factory=list)
    #add caps and floors

@dataclass_json
@dataclass
class ClientRevenuesDeclaration:
    recurring_fixed_revenues:List[RecurringFixedRevenue] = field(default_factory=list) 
    recurring_float_revenues:FloatRevenues = FloatRevenues()
    single_fixed_revenues:List[SingleFixedRevenue]= field(default_factory=list)

@dataclass_json
@dataclass
class ClientConfiguration:
    
    client_code: str
    lbms_configuration: LBMSConfiguration
    products: List[str] = field(default_factory=list)
    revenues:ClientRevenuesDeclaration = ClientRevenuesDeclaration()
   




def LoadClientConfig(client_code):

    s3_client = boto3.client('s3')
    key = client_code+".json"
    data = s3_client.get_object(Bucket=CLIENT_CONFIG_BUCKET, Key=key)
    contents = data['Body'].read()
    return ClientConfiguration.from_json(contents)

def WriteClientConfig(client_config):

    s3_client = boto3.client('s3')
    key = client_config.client_code + ".json"
    data = s3_client.put_object(Bucket=CLIENT_CONFIG_BUCKET, Key=key, Body=client_config.to_json())
    return data

