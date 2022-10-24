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
import pandas as pd

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
class MarketplaceConfiguration:
    marketplace_code:str = ""
    # other stuff to come like percentage of margin kickback


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
class RedemptionPerOptionRevenues:
    classification: RevenueClassification = RevenueClassification()
    currency_code:str = ""
    cost_and_fee_betas_per_option: Dict[str,List[Decimal]] = field(default_factory=Dict)


@dataclass_json
@dataclass
class ClientRevenuesDeclaration:
    recurring_fixed_revenues:List[RecurringFixedRevenue] = field(default_factory=list) 
    recurring_float_revenues:FloatRevenues = FloatRevenues()
    single_fixed_revenues:List[SingleFixedRevenue]= field(default_factory=list)
    redemption_per_option_revenues: List[RedemptionPerOptionRevenues] = field(default_factory=list)

@dataclass_json
@dataclass
class ClientConfiguration:
    
    client_code: str
    
    lbms_configuration: LBMSConfiguration
    marketplace_configuration: MarketplaceConfiguration
    
    products: List[str] = field(default_factory=list)
    
    revenues:ClientRevenuesDeclaration = ClientRevenuesDeclaration()
   



@dataclass
class ClientConfigurationManager:
    client_files_dataframe: pd.DataFrame = pd.DataFrame(columns=['Client','Valid_to','Key'])


    def Init(self):
        s3_client = boto3.client('s3')
        files = s3_client.list_objects_v2(Bucket=CLIENT_CONFIG_BUCKET)
        files_json = files['Contents']
        files = map(lambda f: f['Key'],files_json)
        client_files = filter(lambda f: f.startswith("clients/") and len(f.split('/'))==3 and f.endswith(".json"),files)
        
        items = []
        for file in client_files:
            tokens = file.split("/")
            client = tokens[1]
            f_name = tokens[2]
            if '#' in f_name:
                tok = f_name.split('#')
                validity = tok[1]
                f_token= validity.replace('.json','').split('_')
                items.append({'Client':client, 'Valid_to':f_token[0]+'/'+f_token[1],'Key':file})
            else:
                items.append({'Client':client, 'Valid_to':'Current','Key':file})
            
    
        self.client_files_dataframe = pd.DataFrame(items,columns=['Client','Valid_to','Key'])

    def LoadConfig(self,client,month,year):
        df = self.client_files_dataframe[self.client_files_dataframe['Client']==client]
        # validList = df['Valid_to'].tolist()
        month=int(month)
        year = int(year)
        df =df.set_index('Valid_to')
        valid_list = df.index.tolist()


        selected_index = 'Current'
        selected_month = 1
        selected_year = 3000
        for valid in valid_list:
            if valid == 'Current':
                continue
            else:
  
                tok = valid.split("/")
                stamp_month = int(tok[0])
                stamp_year = int(tok[1])
                if _isOnOrBefore(month,year,stamp_month, stamp_year) and _isOnOrBefore(stamp_month,stamp_year,selected_month,selected_year):
                    selected_month=stamp_month
                    selected_year=stamp_year
                    selected_index = str(selected_month)+'/'+str(selected_year) 

        key = df.at[selected_index,'Key']
        return _loadClientConfig(client,key)

def _loadClientConfig(client_code,key):

    s3_client = boto3.client('s3')
    data = s3_client.get_object(Bucket=CLIENT_CONFIG_BUCKET, Key=key)
    contents = data['Body'].read()
    return ClientConfiguration.from_json(contents)
    

def _isOnOrBefore(month, year, comp_month, comp_year):
    if year < comp_year:
        return True
    if year <= comp_year:
        if month<= comp_month:
            return True
        else:
            return False
    else:
        return False    

                




def WriteClientConfig(client_config):

    s3_client = boto3.client('s3')
    key = client_config.client_code + ".json"
    data = s3_client.put_object(Bucket=CLIENT_CONFIG_BUCKET, Key=key, Body=client_config.to_json())
    return data

