import streamlit as st
import pandas as pd




# def GetClientMapDataFrame():
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

#     df = pd.DataFrame(entries)
#     return df
