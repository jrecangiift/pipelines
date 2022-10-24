import streamlit as st
import pandas as pd


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
            "name": " Bank Danamon",
            "live": True,
            "logo": "..."
        }],
        "Bengladesh": [{
            "code": "EBL",
            "name": " Bank Danamon",
            "live": True,
            "logo": "..."
        }, {
            "code": "MTB",
            "name": " Bank Danamon",
            "live": True,
            "logo": "..."
        }]
    },
    "MENA": {
        "UAE": [
            {
                "code": "CBI",
                "name": " Bank Danamon",
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
        }]
    },
    "North America": {},
    "South America": {},
    "Europe": {}

}


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


def GetClientMapDataFrame():
    entries = []
    for region, v in CLIENT_REGIONAL_CONFIG.items():
        for country, clientList in v.items():
            for client in clientList:
                entries.append(
                    {"Client": client['code'], 
                    "Region": region, 
                    "Country": country, 
                    "Name": client['name'],
                    "Live": client['live'],
                    "Logo": client['logo']
                    })

    df = pd.DataFrame(entries)
    return df
