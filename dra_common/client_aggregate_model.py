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
from revenue_model import RevenueItem
import pandas as pd


AGGREGATE_REPORTING_AWS = 'dra-client-aggregate-data'

class AccrualChannel(str,Enum):
    debit_card = "Debit Card"
    credit_card= "Credit Card"
    insurance= "Insurance"
    casa = "CASA"
    investment = "Investment"
    lending = "Lending"
    e_channels = "E-Channels"
    unknown = "Unknown"

class RedemptionOption(str,Enum):
    gift_card = "Gift Card"
    utility = "Utility"
    exchange = "Points Exchange"
    travel = "Travel"
    shop = "Shop"
    charity = "Charity"
    unknown = "Unknown"
    cancelled = "Cancelled"
    game = "Game"
    auction = "Auction"

@dataclass_json
@dataclass
class ProductAccrual:
    product_code:str
    points_accrued:int = 0
    gmv: Decimal = Decimal(0)
    points_expired:int = 0

@dataclass_json
@dataclass
class PointsAndCount:
    sum:int=0
    count:int=0

@dataclass_json
@dataclass
class Bound:
    low:int =0
    up:int = 0
    amount:int = 0

@dataclass_json
@dataclass
class PointsTiering:
    no_points_amount:int =0
    max_tier_amount:int = 0
    max_tier_value:int = 0
    bounds:List[Bound] = field(default_factory=list)

@dataclass_json
@dataclass
class LBMSState:
    users_points_tiering:PointsTiering = field(default_factory=dict)
    points_points_tiering:PointsTiering = field(default_factory=dict)
    total_points:int =0
    total_users:int =0
    total_users_with_points:int =0
    

@dataclass_json
@dataclass
class CustomersActivity:
    new:int=0
    cancelled:int=0
    activated:int=0
    earned_points:int=0
    activated_and_earned_points:int=0

@dataclass_json
@dataclass
class LBMSMetrics:
    customers_activity:CustomersActivity = field(default_factory=dict)
    points_accrued:int =0
    emails_sent: int =0
    sms_sent:int =0

    
    points_redeemed:int = 0
    
    points_accrued_per_channel: Dict[AccrualChannel,List[ProductAccrual]] = field(default_factory=dict)

    lbms_state: LBMSState = LBMSState()

    points_redeemed_per_internal_category: Dict[str,PointsAndCount] = field(default_factory=dict)
    points_redeemed_per_redemption_option: Dict[str,PointsAndCount] = field(default_factory=dict)

    def GetPointsAccrualDataFrame(self,fx):    
        items = []
        for channel in self.points_accrued_per_channel.keys():
            for product in self.points_accrued_per_channel[channel]:
                items.append({
                    "Channel": channel,
                    "Product": product.product_code,
                    "Points Accrued": product.points_accrued,
                    "Points Accrued ($)": fx.point_to_cst_usd(product.points_accrued),
                    "Points Accrued ("+fx.ccy_code+")":fx.point_value*product.points_accrued,
                    "GMV ("+fx.ccy_code+")":product.gmv,
                    "GMV ($)": fx.local_to_cst_usd(product.gmv),
                    "Points Expired":product.points_expired,                   
                    "Points Expired ($)":fx.point_to_cst_usd(product.points_expired)
                })
        return pd.DataFrame(items)
    

@dataclass_json
@dataclass
class ProductMetrics:
    lbms_metrics: LBMSMetrics = LBMSMetrics()




@dataclass_json
@dataclass
class ClientAggregateReport:
    client_code:str
    month:int
    year:int
    product_metrics: ProductMetrics = ProductMetrics()
    revenues: List[RevenueItem] = field(default_factory=list)
    configuration: ClientConfiguration = field(default_factory=dict)
 
    def GetPointsRedeemedByInternalCategory(self,cat):
        return self.product_metrics.lbms_metrics.points_redeemed_per_internal_category[cat].sum

    def Save(self):
        s3_client = boto3.client('s3')
        key = self.client_code + "@"+str(self.month) + "@"+str(self.year)+".json"
        data = s3_client.put_object(Bucket=AGGREGATE_REPORTING_AWS, Key=key, Body=self.to_json())
        return data

    @staticmethod
    def Load(client_code, month, year):
        s3_client = boto3.client('s3')
        key = client_code+"@"+str(month)+"@"+str(year)+".json"
        data = s3_client.get_object(Bucket=AGGREGATE_REPORTING_AWS, Key=key)
        contents = data['Body'].read()
        report = ClientAggregateReport.from_json(contents)
        return report

    @staticmethod
    def ListAll():
        s3_client = boto3.client('s3')
        files = s3_client.list_objects_v2(Bucket=AGGREGATE_REPORTING_AWS)
        data = {}
        if (files['KeyCount']>0):
            files_json = files['Contents']
            for fi in files_json:
                tok = fi['Key'].split('@')
                period=tok[1]+'/'+ (tok[2].split('.'))[0]
                if tok[0] not in data.keys():
                    data[tok[0]]=[{period: fi['LastModified']}]        
                else:
                    data[tok[0]].append({period: fi['LastModified']})     
            index=[]
            dd=[]
            for client in data.keys():
                index.append(client)
                cd={}
                for v in data[client]:            
                    for k in v:
                        cd[k]=v[k]
                dd.append(cd)
            df = pd.DataFrame(dd, index=index)
            return df

    

    def GetRevenuesDataFrame(self, fx):

        items = []
        for rev in self.revenues:
            items.append({
                "Business Line":rev.classification.business_line,
                "Product Line":rev.classification.product_line,
                "Type":rev.classification.tags["Type"],
                "Label":rev.label,
                "Gross Revenue ("+fx.ccy_code+")":rev.amount,
                "Net Revenue ("+fx.ccy_code+")":rev.amount*(1-rev.net_offset),
                "Gross Revenue ($)":fx.local_to_cst_usd(rev.amount),
                "Net Revenue ($)":fx.local_to_cst_usd(rev.amount)*Decimal(1-rev.net_offset),
                "Revenue Tags":str(rev.classification.tags.values())
            })

        return pd.DataFrame(items)