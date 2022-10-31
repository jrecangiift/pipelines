
import streamlit as st
from streamlit_option_menu import option_menu
from data_loaders import LoadAllAnalytics
from st_aggrid import AgGrid, GridUpdateMode, GridOptionsBuilder, DataReturnMode
import pandas as pd
import numpy as np
from decimal import Decimal
import datetime
from utils import GetPreviousMonth
import plotly.express as px
from PIL import Image
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from styling import k_sep_formatter

from product_lbms_model import LBMSMonthlyData
from product_lbms_controller import BuildMonthlyLBMSData
from datetime import date

import meta_data as md

def format_date(s):
    toks = s.split("/")
    return datetime.date(int(toks[1]),int(toks[0]),1).strftime('%B %Y')

def format_real_date(d):
    try:
        return d.strftime('%D')
    except:
        return "--"

if 'run_all' not in st.session_state:
    st.session_state['run_all'] = False


st.title("🧑‍💻Data Pipelines")
import auth_protocol
auth_protocol.Auth()

if st.session_state["authentication_status"]:

    menu_selection = option_menu(None, ["Product ETLS", "Analytical Layers"], 
    # icons=['file-earmark', 'graph-up', "clipboard-data", 'gear'], 
    menu_icon="cast", default_index=0, orientation="horizontal" )

    if menu_selection == 'Product ETLS':
        col1,col2=st.columns([2,6])
        col1.selectbox("Select a Product",["LBMS","Marketplace"], key="product_selected")

        if st.session_state["product_selected"]=="LBMS":
           
            lbms_monthly = LBMSMonthlyData.ListAll()
            lbms_monthly = lbms_monthly.applymap(format_real_date)
            lbms_monthly = lbms_monthly.reset_index()

            st.markdown("#### Client LBMS Data Monthly Runs")
            AgGrid(lbms_monthly,fit_columns_on_grid_load=True)

            st.markdown("#### Run Locally")

            months = range(13)[1:]
            years = ['2022','2023','2024']

            obj_list = md.GetClientMapList()
            # obj_list.sort()
            client_names = [c['Client'] for c in obj_list]
            col1, col2, col3 = st.columns([1,1,1])
            col1.selectbox(("Client"),client_names,  key="client", disabled= st.session_state["run_all"])     
            col2.selectbox("Month",months, key="month")
            col3.selectbox("Years",years, key="year")   
            col1, col2, col3 = st.columns([1,1,1])
            col1.checkbox("Run all clients",key="run_all")

            run = st.button("Run LBMS Data Pipeline")
            if run:
                if st.session_state["run_all"]:
                    st.write("Not implemented")
                else:
                    try:
                        response = BuildMonthlyLBMSData(st.session_state["client"],st.session_state["month"],st.session_state["year"] )
                        if response =={}:
                            st.error("Run for: {} failed".format(st.session_state["client"]) )
                        else:
                            st.success("Run for: {} succeeded".format(st.session_state["client"]) )
                    except:
                        st.error("Run for: {} failed".format(st.session_state["client"]) + str(Exception))