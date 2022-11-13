from enum import Enum
import pandas as pd
from typing import List
from dataclasses import dataclass
from dataclasses_json import dataclass_json
import boto3

class BusinessLine(str,Enum):
    corporate_loyalty = "Corporate Loyalty"
    merchant_loyalty = "Merchant Loyalty"
    employee_reward = "Employee Loyalty"
    unknown = "Unknown"
    @classmethod
    def list(cls):
        return list(map(lambda c: c.value, cls))

class ProductLine(str,Enum):
    lbms = "LBMS"
    marketplace = "Marketplace"
    box = "Box"
    
    plum = "Plum"
    unknown = "Unknown"


class ServiceType(str,Enum):
    professional_services = "Professional Services"
    marketing = "Marketing"
    prop_offers = "Prop. Offers"
    @classmethod
    def list(cls):
        return list(map(lambda c: c.value, cls))


@dataclass_json
@dataclass
class Client:
    code:str
    region:str
    country:str
    name:str
    live:bool
    logo:str

@dataclass_json
@dataclass
class ClientList:
    clients: List[Client]
    


CLIENT_REGIONAL_CONFIG = {
    "Asia": {
        "Indonesia": [

            {
                "code": "BDI",
                "name": "Bank Danamon Indonesia",
                "live": True,
                "logo": "BDI.png"
            },
            {
                "code": "BNI",
                "name": "Bank Nagara Indonesia",
                "live": True,
                "logo": "BNI.png"
            },
            {
                "code": "BRI",
                "name": "Bank Rakyat Indonesia",
                "live": True,
                "logo": "BRI.png"
            },
            {
                "code": "BJB",
                "name": "Bank Jawa Barat",
                "live": True,
                "logo": "BJB.png"
            },
            {
                "code": "QNB",
                "name": " Bank QNB Indonesia",
                "live": False,
                "logo": "..."
            },

        ],
        "Sri-Lanka": [
            {
                "code": "commbank",
                "name": "Commercial Bank Sri-Lanka",
                "live": True,
                "logo": "commbank.png"
            }

        ],
        "Maldives": [{
            "code": "BML",
            "name": "Bank of Maldives",
            "live": True,
            "logo": "BML.png"
        }],
        "India": [{
            "code": "cardbuzz",
            "name": "CardBuzz",
            "live": True,
            "logo": "..."
        }],
        "Bengladesh": [{
            "code": "EBL",
            "name": "Eastern Bank Limited",
            "live": True,
            "logo": "..."
        }, {
            "code": "MTB",
            "name": "Mutual Trust Bank",
            "live": True,
            "logo": "..."
        }]
    },
    "MENA": {
        "UAE": [
            {
                "code": "CBI",
                "name": "Commercial Bank International",
                "live": True,
                "logo": "..."
            },
            {
                "code": "AHB",
                "name": "Al Hilal Bank",
                "live": False,
                "logo": "..."
            },
            {
                "code": "ADCB",
                "name": "Abu Dhabi Commercial Bank",
                "live": False,
                "logo": "..."
            }],
        "Qatar": [{
            "code": "CBQ",
            "name": "Commercial Bank Qatar",
            "live": False,
            "logo": "..."
        }],
        # "Oman":["OAB"],
        "Kuwait": [{
            "code": "GBK",
            "name": "Gulf Bank Kuwait",
            "live": True,
            "logo": "..."
        }]
    },
    "Africa": {
        "Nigeria": [{
            "code": "UBN",
            "name": "Union Bank Nigeria",
            "live": False,
            "logo": "..."
        }],
        "Rwanda": [{
            "code": "BOK",
            "name": "Bank of Kigali",
            "live": False,
            "logo": "..."
        }],
        "South Africa":[{
            "code": "Visa Africa",
            "name": "Visa Africa",
            "live": True,
            "logo": "..."
        }]
    },
    "North America": {},
    "South America": {},
    "Europe": {}

}

# def GetClientMapList():
#     entries = []
#     for region, v in CLIENT_REGIONAL_CONFIG.items():
#         for country, clientList in v.items():
#             for client in clientList:
#                 entries.append(
#                     {"Client": client['code'],
#                     "Region": region,
#                     "Country": country,
#                     "Name": client['name'],
#                     "Live": client['live'],
#                     "Logo": client['logo']
#                     })
#     return entries

CLIENT_CONFIG_BUCKET = 'dra-config-prod'

def GetClientMapList():
    key="all_clients.json"
    s3_client = boto3.client('s3')
    data = s3_client.get_object(Bucket=CLIENT_CONFIG_BUCKET, Key=key)
    contents = data['Body'].read()
    
    cl_lst = ClientList.from_json(contents)
    lst = cl_lst.clients
    entries = []
    # print(lst)
    for cl in lst:
        entries.append(
              {
                "Client": cl.code,
                "Region": cl.region,
                "Country": cl.country,
                "Name": cl.name,
                "Live": cl.live,
                "Logo": cl.logo
              }
        )
    return entries

def GetClientMapDataFrame():
    entries = GetClientMapList()

    return pd.DataFrame(entries)