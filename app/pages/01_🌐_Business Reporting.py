
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
st.title("🌐 Business Reporting")


def format_date(s):
    toks = s.split("/")
    return datetime.date(int(toks[1]),int(toks[0]),1).strftime('%B %Y')

def dateFunc(s):
    toks = s.split("/")
    date = datetime.datetime(int(toks[1]),int(toks[0]),1)
    return date


def get_dates_list_formatted():
     ### Build the date list with x look_back
    now = datetime.datetime.today()
    lookback_in_months = 6

    list_of_dates = []
    currentMonth = now.month
    currentYear = now.year
    for m in range(lookback_in_months):
        prev = GetPreviousMonth(currentMonth,currentYear)
        currentMonth = prev[0]
        currentYear = prev[1]
        list_of_dates.append(str(currentMonth)+'/'+str(currentYear))
    list_of_dates.sort(key=dateFunc)
    return list_of_dates

def add_line_trace(fig,df,row,col):
    fig.add_trace(
        go.Scatter(
            x=df['Date'],
            y=df['Value'],
            mode="lines"          
        ),row=row, col=col
    )

import auth_protocol
auth_protocol.Auth()
if st.session_state["authentication_status"]:

    list_of_dates = get_dates_list_formatted()
    # print(list_of_dates)
    # date_selected = st.sidebar.selectbox("Pick Date",list_of_dates, index = len(list_of_dates)-1, label_visibility="collapsed", format_func=format_date)

    # toks = date_selected.split("/")
    # st.session_state["month_selected"]=toks[0]
    # st.session_state["year_selected"]=toks[1]

    menu_selection = option_menu(None, ["Group Revenues",  "Products", 'Services'], 
            icons=['file-earmark', "clipboard-data", 'gear'], 
            menu_icon="cast", default_index=0, orientation="horizontal" )

    if menu_selection == "Group Revenues":
        
    # This is where we pull all analytics objects with metrics and revenue data - we merge and display

    # Client Analytics (covers Giift products and services)

        analytics = LoadAllAnalytics()


        rev_aggregation_levels = ['Business Line', 'Product', 'Revenue Type']
        revenue_aggregation_level = 'Product'
        # st.dataframe(analytics.revenue_frame)

        rev_frame = analytics.revenue_frame

        rev_frame['Net Amount ($)'] = rev_frame['Net Amount ($)'].apply(lambda x: Decimal(x))
        st.write("----")
        col1, col2, col3, col4 = st.columns([1,1,3,1])
        image = Image.open('assets/Giift.png')
        col2.image(image, width=130)
        col3.markdown("## Group Revenues Reporting")

        
        col1, col2, = st.columns([3,5])
        
        col1.radio("Select Aggregation Level",rev_aggregation_levels,horizontal=True,key="rev_agg_level_selected")
        # col1.write("----")
        col2.checkbox("Cumulative", key="cumulative",help="Monthly or cumulative on the period")
       
        
        df2 = rev_frame.groupby([st.session_state["rev_agg_level_selected"],'Date'])['Net Amount ($)'].sum().reset_index()

        fig = px.line(df2, x="Date", y="Net Amount ($)", color=st.session_state["rev_agg_level_selected"],width=1000)

        
        st.plotly_chart(fig)

        with st.expander("Underlying Data"):
            AgGrid(df2) 
    
    if menu_selection == "Products":
        col1,col2=st.columns([2,6])
        col1.selectbox("Select a Product",["LBMS","Marketplace"], key="product_selected")

        analytics = LoadAllAnalytics()

        if st.session_state["product_selected"]=="LBMS":
            # st.write(st.session_state["product_selected"])

            # Reporting on LBMS Key metrics

            metrics = analytics.main_frame

            lbms_metrics = metrics[(metrics["Product"] == "LBMS")]
            # AgGrid(lbms_metrics)

            df = lbms_metrics.groupby(['Identifier','Date'])['Value'].sum().reset_index()

            df.set_index(['Identifier'],inplace=True)

            

            with st.expander("Revenues & Points Financials"):         
                fig = make_subplots(
                        rows=2, cols=2,
                        shared_xaxes=True,
                        x_title='Date',
                        vertical_spacing=0.07,
                        subplot_titles=[("Net Revenues ($)"),("Points Accrued ($)"),("Points Redeemed ($)"),("Total Points Liability ($)")]
                )
                add_line_trace(fig,df.loc['net_revenues',:],1,1)
                add_line_trace(fig,df.loc['points_accrued_std_usd',:],1,2)
                add_line_trace(fig,df.loc['points_redeemed_std_usd',:],2,1)
                add_line_trace(fig,df.loc['total_points_std_usd',:],2,2)

                fig.update_layout(height=600, width=1200,showlegend=False )
      
                st.plotly_chart(fig)

                # accrual_gmv = df[(df['Identifier']=='accrual_gmv')]

                # fig = px.line(accrual_gmv,x="Date", y="Value")
                # st.plotly_chart(fig)

            with st.expander("Accruals"):
                # st.write("OK")

                accrual_frame = analytics.lbms_accruals  

                df_acc = accrual_frame.groupby(['Channel','Date'])['Points Accrued ($)'].sum().reset_index()
                df_acc["Date"] = df_acc["Date"].apply(dateFunc)
                df_acc.sort_values(by='Date',inplace=True)
                fig = px.line(df_acc, x='Date', y='Points Accrued ($)', color='Channel')    
                st.plotly_chart(fig)        

          
                gb = GridOptionsBuilder.from_dataframe(df_acc)
                gb.configure_default_column(enablePivot=True, enableValue=True, enableRowGroup=True)
                gb.configure_side_bar()
                
                gb.configure_column("Date",rowGroup=True,hide=True, rowGroupIndex= 0)
                # gb.configure_column("Channel",rowGroup=True,hide=True, rowGroupIndex= 1)
                
                gb.configure_column("Points Accrued ($)", aggFunc="sum",type=["numericColumn"], precision=0,valueFormatter=k_sep_formatter)
                # gb.configure_column("Points Accrued ($)", aggFunc="sum",type=["numericColumn"], precision=0,valueFormatter=k_sep_formatter)
                # gb.configure_column("Points Expired ($)", aggFunc="sum",type=["numericColumn"], precision=0,valueFormatter=k_sep_formatter)
                gridoptions = gb.build()
                response = AgGrid(
                    df_acc,
                    gridOptions=gridoptions,
                    height=500,
                    enable_enterprise_modules=True,
                    update_mode=GridUpdateMode.NO_UPDATE,
                    fit_columns_on_grid_load=True,
                    header_checkbox_selection_filtered_only=True,
                    allow_unsafe_jscode=True
                    )

            with st.expander("Redemptions"):
                # st.write("OK")

                red_frame = analytics.lbms_redemptions
                # red_frame.sort_values(by='Date',inplace=True)

                # red_frame["real_date"] = red_frame["Date"].apply(dateFunc)
                # AgGrid(red_frame)
                df_red = red_frame.groupby(['Redemption Option','Date'])['Points Redeemed ($)'].sum().reset_index()

                df_red["Date"] = df_red["Date"].apply(dateFunc)
                df_red.sort_values(by='Date',inplace=True)
                

                fig = px.line(df_red, x='Date', y='Points Redeemed ($)', color='Redemption Option')    
                st.plotly_chart(fig)     




                gb = GridOptionsBuilder.from_dataframe(df_red)
                gb.configure_default_column(enablePivot=True, enableValue=True, enableRowGroup=True)
                gb.configure_side_bar()
                
                gb.configure_column("Date",rowGroup=True,hide=True, rowGroupIndex= 0)
                # gb.configure_column("Redemption Option",rowGroup=True,hide=True, rowGroupIndex= 1)
                
                gb.configure_column("Points Redeemed ($)", aggFunc="sum",type=["numericColumn"], precision=0,valueFormatter=k_sep_formatter)
                # gb.configure_column("Points Accrued ($)", aggFunc="sum",type=["numericColumn"], precision=0,valueFormatter=k_sep_formatter)
                # gb.configure_column("Points Expired ($)", aggFunc="sum",type=["numericColumn"], precision=0,valueFormatter=k_sep_formatter)
                gridoptions = gb.build()
                response = AgGrid(
                    df_red,
                    gridOptions=gridoptions,
                    height=500,
                    enable_enterprise_modules=True,
                    update_mode=GridUpdateMode.NO_UPDATE,
                    fit_columns_on_grid_load=True,
                    header_checkbox_selection_filtered_only=True,
                    allow_unsafe_jscode=True
                    )

          



            with st.expander("Users"):   
                fig = make_subplots(
                        rows=1, cols=2,
                        shared_xaxes=True,
                        x_title='Date',
                        vertical_spacing=0.07,
                        subplot_titles=[("Users"),("Monthly Active Users")]
                )
                add_line_trace(fig,df.loc['total_users',:],1,1)
                add_line_trace(fig,df.loc['accrual_active_users',:],1,2)
                fig.update_layout(height=400, width=1200,showlegend=False )
           
                st.plotly_chart(fig)
                






    






        if st.session_state["product_selected"]=="Marketplace":
            st.write(st.session_state["product_selected"])