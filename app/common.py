import streamlit as st
import pandas as pd

STD_CCY_FX={
    "IDR":0.000067,
    "AED":0.35,
    "USD":1,
    "QAR":0.27,
    "BDT":0.0096,
    "LKR":0.0028,
    "OMR":2.60,
    "MVR":0.65,
    "INR":0.012,
    "KWD":3.23



}

CLIENT_REGIONAL_CONFIG ={
    "Asia":{
        "Indonesia": ["BDI","BNI","BRI","BJB",'QNB'],
        # "Sri-Lanka": ["EBL", "MTB"],
        "India": ["cardbuzz"]    
    },
    "MENA":{
        "UAE":["CBI"],
        # "Qatar":["CBQ", "QIB", "ABQ"],
        # "Oman":["OAB"],
        "Kuwait":["GBK"]
    },
    "Africa":{
        # "Nigeria":["UBN"],
        # "Rwanda":["BOK"]
    },
    "North America":{},
    "South America":{},
    "Europe":{}
    
}


def GetPreviousMonth(month, year):
    if month==1:
        return [12,year-1]
    else:
        return [month-1,year]

def AddToDic(dic,key, num):
    if key in dic:
        dic[key]+=num
    else:
        dic[key]=num


def GetClientMapDataFrame():
    entries = []
    for region, v in CLIENT_REGIONAL_CONFIG.items():
        for country, clientList in v.items():
            for client in clientList:
                entries.append({"Client":client,"Region":region,"Country":country})
    
    df = pd.DataFrame(entries)
    return df




