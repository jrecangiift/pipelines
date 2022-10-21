
from curses import meta
import streamlit as st
import datetime
import sys


from decimal import Decimal

from common import GetPreviousMonth,CLIENT_REGIONAL_CONFIG, GetClientMapDataFrame
from st_aggrid import AgGrid, GridUpdateMode, GridOptionsBuilder, DataReturnMode
import plotly.express as px
import client_aggregate_model as cam
from fx_conversion import FXConverter
from client_aggregate_model import LBMSMetrics
from client_aggregate_analytics import ClientsAggregateAnalytics

st.set_page_config(layout="wide")
from styling import k_sep_formatter


if 'selected_client' not in st.session_state:
    st.session_state['selected_client'] = 'N/A'
if 'active' not in st.session_state:
    st.session_state['active'] = False

prev_loaded = False
NO_DECIMAL = Decimal(10) ** -0
THREE_DECIMAL = Decimal(10) ** -3
@st.cache
def fetch_client_reports_list():
    return cam.ClientAggregateReport.ListAll()

@st.cache
def fetch_client_report(client_code, month,year):
    try:
        return cam.ClientAggregateReport.Load(client_code, month,year)
    except:
        return 0

def dateFunc(s):
    toks = s.split("/")
    date = datetime.datetime(int(toks[1]),int(toks[0]),1)
    return date

def format_date(s):
    toks = s.split("/")
    return datetime.date(int(toks[1]),int(toks[0]),1).strftime('%B %Y')

# relies on global variables being set correctly:
# client & caa
def get_lbms_metrics(date,identifier):
    return caa.GetMetrics(client, date,"Corporate Loyalty","LBMS",identifier)

def get_lbms_metrics_rel_perf(date_from,date_to,identifier):
    return caa.GetMetricsRelativePerf(client, date_from,date_to,"Corporate Loyalty","LBMS",identifier)

NO_DECIMAL = Decimal(10) ** -0

v=[]
response={}
def updateClient():
    v=response['selected_rows']
    st.session_state["selected_client"]=v[0]["Client"]


df_client_map = GetClientMapDataFrame()
with st.sidebar:

    col1, col2 = st.sidebar.columns(2)

    col1.markdown("# Client Reporting" )
    gb = GridOptionsBuilder.from_dataframe(df_client_map)
    gb.configure_selection(selection_mode="single", use_checkbox=False, header_checkbox=False)
    gridoptions = gb.build()

    response = AgGrid(
        df_client_map,
        gridOptions=gridoptions,
        height=400,
        enable_enterprise_modules=True,
        update_mode=GridUpdateMode.SELECTION_CHANGED,
        data_return_mode=DataReturnMode.FILTERED_AND_SORTED,
        fit_columns_on_grid_load=True,
        header_checkbox_selection_filtered_only=False,
        use_checkbox=False,
        onclick=updateClient)

    v = response['selected_rows']
    if len(v)>0:
        client_selected = v[0]["Client"]
 
        st.session_state["client_selected"] = client_selected

# No client selected yet
if  len(v)==0:
    st.header("Select A Client")

# Client is selected - run report script
if  len(v)>0:    
    st.session_state["active"]=True
    aggregate = fetch_client_reports_list()
    ds= (aggregate.loc[st.session_state["client_selected"]])
    ds=ds.dropna()

    dateList = (ds.keys().tolist())
    dateList.sort(key=dateFunc)
    c1,c2 = st.columns([1,5])
    date_selected = st.sidebar.selectbox(st.session_state["client_selected"],dateList, index = len(dateList)-1, label_visibility="collapsed", format_func=format_date)
    toks = date_selected.split("/")
    st.session_state["month_selected"]=toks[0]
    st.session_state["year_selected"]=toks[1]
    if st.sidebar.button("Clear Cache"):
        st.runtime.legacy_caching.clear_cache()
    
    momTab, trendsTab, tabExperimental = st.tabs(["Monthly Report", "Over Time", "Advanced Analytics"])
    
    with momTab:

        caa = ClientsAggregateAnalytics()
        prev = GetPreviousMonth(int(st.session_state["month_selected"]),int(st.session_state["year_selected"]))
        client = st.session_state["client_selected"]
        spotDate = st.session_state["month_selected"]+"/"+st.session_state["year_selected"]
        prevDate = str(prev[0])+"/"+str(prev[1])
        spotReport = fetch_client_report(client,st.session_state["month_selected"],st.session_state["year_selected"])
        prevReport = fetch_client_report(client,prev[0],prev[1])
        caa.PushReport(spotReport)
        if prevReport!=0:
            caa.PushReport(prevReport)

        # AgGrid(caa.main_frame)

        st.subheader(":sparkles:Dashboard")

        ###### previous month not available
        if prevReport==0:
            st.markdown("##### :red_circle:Key Account Performance Indicators")
          
            col1, col2, col3,col4 = st.columns(4)
            col1.metric("Take Rate (basis points)",'{:.2f} bp'.format(get_lbms_metrics(spotDate,"take_rate")*10000))
            col2.metric("Net Revenue Per MAU ($)",'{:.5f}'.format(get_lbms_metrics(spotDate,"net_revenue_per_active_user")))     
            col3.metric("MAU Over TU",'{:.1f}%'.format(100*get_lbms_metrics(spotDate,"accrual_engagement_rate")))
            col4.metric("Net Revenues ($)" , "{:,.0f}".format(get_lbms_metrics(spotDate,"net_revenues")))

            st.markdown("##### :large_blue_circle:Key Account Metrics")
            
            col1, col2, col3 = st.columns(3) 
            col1.metric("Total Points Value ($)", "{:,.0f}".format(get_lbms_metrics(spotDate,"total_points")))
            col2.metric("Total Users" , "{:,.0f}".format(get_lbms_metrics(spotDate,"total_users")))  
            col3.metric("Monthly Active Users (MAU)", "{:,.0f}".format(get_lbms_metrics(spotDate,"active_users")))
            
            col1, col2, col3 = st.columns(3)
            col1.metric("Points Accrued Value ($)", "{:,.0f}".format(get_lbms_metrics(spotDate,"points_accrued")))
            col2.metric("Points Redeemed Value ($)",  "{:,.0f}".format((get_lbms_metrics(spotDate,"points_redeemed"))))
            col3.metric("GMV ($)" , "{:,.0f}".format(get_lbms_metrics(spotDate,"accrual_gmv")))
            
        # ###### previous month is available
        else:
            st.markdown("##### :red_circle:Key Account Performance Indicators")
            
            col1, col2, col3,col4 = st.columns(4)
            col1.metric("Take Rate (basis points)",'{:.2f} bp'.format(get_lbms_metrics(spotDate,"take_rate")*10000), '{:.2f}%'.format(get_lbms_metrics_rel_perf(prevDate,spotDate,"take_rate")))
            col2.metric("Net Revenue Per MAU ($)",'{:.5f}'.format(get_lbms_metrics(spotDate,"net_revenue_per_active_user")), '{:.2f}%'.format(get_lbms_metrics_rel_perf(prevDate,spotDate,"net_revenue_per_active_user")))     
            col3.metric("MAU Over TU",'{:.1f}%'.format(100*get_lbms_metrics(spotDate,"accrual_engagement_rate")), '{:.2f}%'.format(get_lbms_metrics_rel_perf(prevDate,spotDate,"accrual_engagement_rate")))
            col4.metric("Net Revenues ($)" , "{:,.0f}".format(get_lbms_metrics(spotDate,"net_revenues")), '{:.2f}%'.format(get_lbms_metrics_rel_perf(prevDate,spotDate,"net_revenues")))

            st.markdown("##### :large_blue_circle:Key Account Metrics")
            
            col1, col2, col3 = st.columns(3) 
            col1.metric("Total Points Value ($)", "{:,.0f}".format(get_lbms_metrics(spotDate,"total_points")), '{:.2f}%'.format(get_lbms_metrics_rel_perf(prevDate,spotDate,"total_points")))
            col2.metric("Total Users" , "{:,.0f}".format(get_lbms_metrics(spotDate,"total_users")), '{:.2f}%'.format(get_lbms_metrics_rel_perf(prevDate,spotDate,"total_users")))  
            col3.metric("Monthly Active Users (MAU)", "{:,.0f}".format(get_lbms_metrics(spotDate,"active_users")), '{:.2f}%'.format(get_lbms_metrics_rel_perf(prevDate,spotDate,"active_users")))
            
            col1, col2, col3 = st.columns(3)
            col1.metric("Points Accrued Value ($)", "{:,.0f}".format(get_lbms_metrics(spotDate,"points_accrued")), '{:.2f}%'.format(get_lbms_metrics_rel_perf(prevDate,spotDate,"points_accrued")))
            col2.metric("Points Redeemed Value ($)",  "{:,.0f}".format((get_lbms_metrics(spotDate,"points_redeemed"))), '{:.2f}%'.format(get_lbms_metrics_rel_perf(prevDate,spotDate,"points_redeemed")))
            col3.metric("GMV ($)" , "{:,.0f}".format(get_lbms_metrics(spotDate,"accrual_gmv")), '{:.2f}%'.format(get_lbms_metrics_rel_perf(prevDate,spotDate,"accrual_gmv")))
            
        st.markdown("""---""")
        st.subheader(":arrow_heading_up:Accruals")

        # AgGrid(caa.lbms_accruals)
        df_acc = caa.lbms_accruals[caa.lbms_accruals["Date"]==spotDate]
        
        df_acc["GMV ($)"]= df_acc["GMV ($)"].apply(lambda x: x.quantize(NO_DECIMAL))
        df_acc["Points Accrued ($)"]= df_acc["Points Accrued ($)"].apply(lambda x: x.quantize(NO_DECIMAL))
        df_acc["Points Expired ($)"]= df_acc["Points Expired ($)"].apply(lambda x: x.quantize(NO_DECIMAL))
        with st.expander("Accrual Data"):
        
            
            gb = GridOptionsBuilder.from_dataframe(df_acc)
            gb.configure_default_column(enablePivot=True, enableValue=True, enableRowGroup=True)
            gb.configure_side_bar()
            gb.configure_column("Client",hide=True)
            gb.configure_column("Date",hide=True)
            gb.configure_column("Channel",rowGroup=True,hide=True, rowGroupIndex= 0)
            gb.configure_column("GMV ($)", aggFunc="sum",type=["numericColumn"], precision=0,valueFormatter=k_sep_formatter)
            gb.configure_column("Points Accrued ($)", aggFunc="sum",type=["numericColumn"], precision=0,valueFormatter=k_sep_formatter)
            gb.configure_column("Points Expired ($)", aggFunc="sum",type=["numericColumn"], precision=0,valueFormatter=k_sep_formatter)
            gridoptions = gb.build()
            response = AgGrid(
                df_acc,
                gridOptions=gridoptions,
                height=300,
                enable_enterprise_modules=True,
                update_mode=GridUpdateMode.NO_UPDATE,
                fit_columns_on_grid_load=False,
                header_checkbox_selection_filtered_only=True,
                allow_unsafe_jscode=True
                )

        with st.expander("Accrual Plots"):

            col1, col2 = st.columns(2)   
            fig = px.sunburst(df_acc[["Channel","Points Accrued ($)", "Product"]], path=['Channel', 'Product'], values="Points Accrued ($)",
            color="Channel", hover_data=["Points Accrued ($)"])
            col1.plotly_chart(fig)
            fig2 = px.scatter(df_acc[["Channel","Points Accrued ($)", "GMV ($)"]], x="Points Accrued ($)", y="GMV ($)", color="Channel")
            col2.plotly_chart(fig2)

        st.markdown("""---""")
        st.subheader("	:arrow_heading_down:Redemptions")

        df_red = caa.lbms_redemptions[caa.lbms_redemptions["Date"]==spotDate]

        df_red["Average Transaction ($)"] = df_red["Points Redeemed ($)"]/df_red["Number Transactions"]
        df_red["Points Redeemed ($)"]= df_red["Points Redeemed ($)"].apply(lambda x: x.quantize(NO_DECIMAL))
        
        with st.expander("Redemption Data"):
        
            
            gb = GridOptionsBuilder.from_dataframe(df_red)
            gb.configure_default_column(enablePivot=True, enableValue=True, enableRowGroup=True)
            gb.configure_side_bar()
            gb.configure_column("Client",hide=True)
            gb.configure_column("Date",hide=True)
            gb.configure_column("Average Transaction ($)")
            gb.configure_column("Redemption Option")
            gb.configure_column("Points Redeemed ($)", aggFunc="sum",type=["numericColumn"], precision=0,valueFormatter=k_sep_formatter)
            gb.configure_column("Number Transactions", aggFunc="sum",type=["numericColumn"], precision=0,valueFormatter=k_sep_formatter)
            
            gridoptions = gb.build()
            response = AgGrid(
                df_red,
                gridOptions=gridoptions,
                height=300,
                enable_enterprise_modules=True,
                update_mode=GridUpdateMode.NO_UPDATE,
                fit_columns_on_grid_load=False,
                header_checkbox_selection_filtered_only=True,
                allow_unsafe_jscode=True
                )

        with st.expander("Redemption Plots"):  

            col1, col2 = st.columns(2)   
            fig1 = px.bar(df_red, x="Redemption Option", y="Points Redeemed ($)", color="Redemption Option", title="Redemptions by Option")
            fig1.update_layout(barmode='relative')
            col1.plotly_chart(fig1)  
            fig2 = px.scatter(df_red[["Redemption Option","Points Redeemed ($)","Average Transaction ($)", "Number Transactions"]], 
            x="Number Transactions", y="Average Transaction ($)", color="Redemption Option")
            col2.plotly_chart(fig2)

        st.markdown("""---""")
        st.subheader(":family:Point Value Analytics")

        df_up = caa.lbms_users_points[caa.lbms_users_points["Date"]==spotDate]
        df_up["Average $ Point Value per User"]= df_up["Points Value ($)"] / df_up["Number Users"]
        df_up["Points Value ($)"]= df_up["Points Value ($)"].apply(lambda x: x.quantize(NO_DECIMAL))
        df_up["Average $ Point Value per User"]= df_up["Average $ Point Value per User"].apply(lambda x: x.quantize(THREE_DECIMAL))
        with st.expander("Point Value Analytics Data"):
            
            gb = GridOptionsBuilder.from_dataframe(df_up)
            gb.configure_default_column(enablePivot=True, enableValue=True, enableRowGroup=True)
            gb.configure_side_bar()
            gb.configure_column("Client",hide=True)
            gb.configure_column("Date",hide=True)
            gb.configure_column("Points Value Threashold ($)",hide=True)
            gb.configure_column("Points Value ($)",aggFunc="sum",type=["numericColumn"], precision=0,valueFormatter=k_sep_formatter)

            
            gridoptions = gb.build()
            response = AgGrid(
                df_up,
                gridOptions=gridoptions,
                height=300,
                enable_enterprise_modules=True,
                update_mode=GridUpdateMode.NO_UPDATE,
                fit_columns_on_grid_load=False,
                header_checkbox_selection_filtered_only=True,
                allow_unsafe_jscode=True
                )
        

        with st.expander("Point Value Analytics Chart"):
            st.write("OK")
