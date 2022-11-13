
import streamlit as st
from cmath import log, nan
from curses import meta
import streamlit as st
import datetime
import sys
from decimal import Decimal
from utils import GetPreviousMonth
from meta_data import GetClientMapDataFrame
from st_aggrid import AgGrid, GridUpdateMode, GridOptionsBuilder, DataReturnMode

import warnings 

from product_marketplace_model import MarketplaceReport

warnings.filterwarnings('ignore')



def dateFunc(s):
    toks = s.split("/")
    date = datetime.datetime(int(toks[1]),int(toks[0]),1)
    return date

def format_date(s):
    toks = s.split("/")
    return datetime.date(int(toks[1]),int(toks[0]),1).strftime('%B %Y')


 ### Build the date list with x look_back

st.title("🛍️ Marketplace Analytics")


import auth_protocol
auth_protocol.Auth()
if st.session_state["authentication_status"]:


    ### Build the date list with x look_back
    now = datetime.datetime.today()
    lookback_in_months = 7

    list_of_dates = []
    currentMonth = now.month
    currentYear = now.year
    list_of_dates.append(str(currentMonth)+'/'+str(currentYear))
    for m in range(lookback_in_months):
        prev = GetPreviousMonth(currentMonth,currentYear)
        currentMonth = prev[0]
        currentYear = prev[1]
        list_of_dates.append(str(currentMonth)+'/'+str(currentYear))
    list_of_dates.sort(key=dateFunc)
    firstDate = list_of_dates[0]

    df_client_map = GetClientMapDataFrame()
    with st.sidebar:

        date_selected = st.sidebar.selectbox("Pick Date",list_of_dates, index = len(list_of_dates)-1, label_visibility="collapsed", format_func=format_date)
        toks = date_selected.split("/")
        st.session_state["month_selected"]=toks[0]
        st.session_state["year_selected"]=toks[1]


# display margins and markups

    report = MarketplaceReport.Load(st.session_state["month_selected"],st.session_state["year_selected"])

    AgGrid(report.margins_frame)
    AgGrid(report.markups_det_frame)