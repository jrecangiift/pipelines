
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
from styling import k_sep_formatter
from product_marketplace_model import MarketplaceReport
import plotly.express as px
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


    report = MarketplaceReport.Load(st.session_state["month_selected"],st.session_state["year_selected"])

    all_transactions = report.all_transactions_frame

# display margins and markups

        # Supplier Analysis
    col1,col2,col3 = st.columns(3)

    total_margins = all_transactions['Margins ($)'].sum()
    total_transactions = all_transactions['Margins ($)'].count()
    col1.metric("Total Margins",'$ {:,.0f}'.format((total_margins)))
    col2.metric("Total Transactions",'{:,.0f}'.format((total_transactions)))

    col1,col2 = st.columns(2)


    fig2 = px.sunburst(all_transactions[["Redemption Option","Category","Margins ($)"]], path=["Redemption Option","Category"], values="Margins ($)",
    color="Redemption Option", hover_data=["Margins ($)"],height=500,width=500,title="Margins per Option & Category")


    
    col1.plotly_chart(fig2)

    total_margins_per_supp = all_transactions.groupby(['Supplier'])['Margins ($)'].sum().to_frame().reset_index()
    
    
    margin_per_client_and_supp = all_transactions.groupby(['Supplier','Client'])['Margins ($)'].sum().to_frame().reset_index()
    sorted = margin_per_client_and_supp.sort_values(by=['Margins ($)'], ascending=False)
    
    fig1 = px.bar(sorted.head(10), color="Client", x="Supplier",
                y="Margins ($)",
                title="Top 10 Suppliers by Margin ($)",
                height=500,
                width=500, 
                )

    col2.plotly_chart(fig1)
    

    col1,col2 = st.columns(2)

    margin_per_client_and_supp = all_transactions.groupby(['Redemption Option','Client'])['Margins ($)'].sum().to_frame().reset_index()
    sorted = margin_per_client_and_supp.sort_values(by=['Margins ($)'], ascending=False)
    
    fig3 = px.bar(sorted.head(10), color="Client", x="Redemption Option",
                y="Margins ($)",
                title="Top 10 Redemption Options by Margin ($)",
                height=500,
                width=500, 
                )

    col1.plotly_chart(fig3)

    amount_per_client_and_supp = all_transactions.groupby(['Redemption Option','Client'])['Amount ($)'].sum().to_frame().reset_index()
    sorted = amount_per_client_and_supp.sort_values(by=['Amount ($)'], ascending=False)
    
    fig4 = px.bar(sorted.head(10), color="Client", x="Redemption Option",
                y="Amount ($)",
                title="Top 10 Redemption Options by Volume ($)",
                height=500,
                width=500, 
                )
    col2.plotly_chart(fig4)
    
    AgGrid(margin_per_client_and_supp)


    gb = GridOptionsBuilder.from_dataframe(all_transactions)
    gb.configure_default_column(enablePivot=True, enableValue=True, enableRowGroup=True)
    gb.configure_side_bar()
    gb.configure_column("Margins ($)",aggFunc="sum",type=["numericColumn"], precision=2,valueFormatter=k_sep_formatter)
    gb.configure_column("Amount ($)",aggFunc="sum",type=["numericColumn"], precision=2,valueFormatter=k_sep_formatter)
    gb.configure_column("Redemption Option",rowGroupIndex=0,hide=True)
    gb.configure_column("Category",rowGroupIndex=1,hide=True)
    gb.configure_column("Client",hide=True)
    gb.configure_column("Client Currency",hide=True)
    gb.configure_column("Client Amount",hide=True)
    gb.configure_column("Product Currency",hide=True)
    gb.configure_column("Date",hide=True)
    
    
    gridoptions = gb.build()
    response = AgGrid(
        all_transactions,
        gridOptions=gridoptions,
        height=500,
        enable_enterprise_modules=True,
        update_mode=GridUpdateMode.NO_UPDATE,
        fit_columns_on_grid_load=False,
        header_checkbox_selection_filtered_only=True,
        allow_unsafe_jscode=True,
        license_key=st.secrets["aggrid_license"]
        )




    
    # AgGrid(total_margins_per_supp.to_frame().reset_index())