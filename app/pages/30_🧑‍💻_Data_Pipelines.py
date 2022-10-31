
import streamlit as st
from streamlit_option_menu import option_menu
from data_loaders import LoadAllAnalytics
from st_aggrid import AgGrid, GridUpdateMode, GridOptionsBuilder, DataReturnMode
import pandas as pd
import numpy as np
from decimal import Decimal
import datetime
from clients_analytics_manager import ClientAnalyticsManager
from product_marketplace_controller import BuildMarketplaceReport
from utils import GetPreviousMonth
import plotly.express as px
from PIL import Image
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from styling import k_sep_formatter

from product_lbms_model import LBMSMonthlyData
from product_lbms_controller import BuildMonthlyLBMSData
from product_marketplace_model import MarketplaceReport
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

if "lbms_monthly" not in st.session_state:
    st.session_state["lbms_monthly"] = pd.DataFrame()


st.title("🧑‍💻Data Pipelines")

import auth_protocol
auth_protocol.Auth()

if st.session_state["authentication_status"]:

    months = range(13)[1:]
    years = ['2022','2023','2024']
    menu_selection = option_menu(None, ["Products ETL", "Analytical Layers"], 
    # icons=['file-earmark', 'graph-up', "clipboard-data", 'gear'], 
    menu_icon="cast", default_index=0, orientation="horizontal" )

    if menu_selection == 'Products ETL':
        col1,col2=st.columns([2,6])
        col1.selectbox("Select a Product",["LBMS","Marketplace"], key="product_selected")

        if st.session_state["product_selected"]=="LBMS":
           

            st.markdown("#### Client LBMS Data Monthly Runs")

            if st.button("Refresh"):

                lbms_monthly = LBMSMonthlyData.ListAll()
                lbms_monthly = lbms_monthly.applymap(format_real_date)
                lbms_monthly = lbms_monthly.reset_index()
                st.session_state["lbms_monthly"]=lbms_monthly

                

            AgGrid(st.session_state["lbms_monthly"],fit_columns_on_grid_load=True)

            st.markdown("#### Run Locally")



            obj_list = md.GetClientMapList()
            clients_frame = md.GetClientMapDataFrame()


            gb = GridOptionsBuilder.from_dataframe(clients_frame)
            gb.configure_selection(selection_mode="multiple", use_checkbox=True, header_checkbox=True)
            gb.configure_default_column(enablePivot=True, enableValue=True, enableRowGroup=True)
            gb.configure_column("Region",rowGroup=True,hide=True, rowGroupIndex= 0)
            # gb.configure_column("month",rowGroup=True,hide=True, rowGroupIndex= 1)
            # gb.configure_column("Live",hide=True )
            gb.configure_column("Logo",hide=True)
            gb.configure_column("uuid",hide=True)
            gridoptions = gb.build()
            
            response = AgGrid(
                clients_frame,
                gridOptions=gridoptions,
                height=500,
                enable_enterprise_modules=True,
                update_mode=GridUpdateMode.SELECTION_CHANGED,
                data_return_mode=DataReturnMode.FILTERED_AND_SORTED,
                fit_columns_on_grid_load=True,
                header_checkbox_selection_filtered_only=True,
                allow_unsafe_jscode=True,
                use_checkbox=True)

          

            selected_list = [r['Client'] for r in response['selected_rows']]

            # st.write(selected_list)

            col1, col2, col3 = st.columns([2,2,1])
            col1.selectbox("Month",months, key="month")
            col2.selectbox("Years",years, key="year")   
            run = st.button("Run LBMS Data Pipeline")

            if run:
                for client in selected_list:
                    try:
                        response = BuildMonthlyLBMSData(client,st.session_state["month"],st.session_state["year"] )
                        if response =={}:
                            st.error("Run for: {} failed".format(client) )
                        else:
                            st.success("Run for: {} succeeded".format(client) )
                    except:
                        st.error("Run for: {} failed".format(client) + str(Exception))

        if st.session_state["product_selected"]=="Marketplace":
         

            st.markdown("#### Marketplace Data Monthly Runs") 
            mktplace_list = MarketplaceReport.ListAll()
            st.write(mktplace_list)
            col1, col2, col3 = st.columns([2,2,1])
            col1.selectbox("Month",months, key="month")
            col2.selectbox("Years",years, key="year")  
            run = st.button("Run Marketplace Data Pipeline")
            if run:
                try:
                    report = BuildMarketplaceReport(st.session_state["month"],st.session_state["year"] )
                    st.success("Run successful" )
                    AgGrid(report.margins_frame)
                    AgGrid(report.markups_det_frame)
                except:
                    st.success("Run failed" )

    if menu_selection == 'Analytical Layers':

        st.markdown("#### Clients Analytics Monthly Runs") 
        cam =ClientAnalyticsManager()
        mktplace_list = cam.ListAll()
        st.write(mktplace_list)
        col1, col2, col3 = st.columns([2,2,1])
        col1.selectbox("Month",months, key="month")
        col2.selectbox("Years",years, key="year")  
        run = st.button("Run Clients Analytics")
        if run:
            try:
                analytics = cam.BuildMonthlyClientAnalytics(st.session_state["month"],st.session_state["year"] )
                st.success("Run successful" )
                AgGrid(analytics.main_frame)
                AgGrid(analytics.push_execution_frame   )
            except:
                st.success("Run failed" )
