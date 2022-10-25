
from cmath import log, nan
from curses import meta
from turtle import title, width
import streamlit as st
import datetime
import sys
from decimal import Decimal
from common import GetPreviousMonth,CLIENT_REGIONAL_CONFIG, GetClientMapDataFrame
from st_aggrid import AgGrid, GridUpdateMode, GridOptionsBuilder, DataReturnMode
import plotly.express as px
import logging as lg
from PIL import Image
from fx_conversion import FXConverter
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import traceback

from product_lbms_model import LBMSMonthlyData
from clients_analytics import ClientsAnalytics
from client_configuration_model import ClientConfigurationManager,ClientConfiguration
from product_marketplace_model import MarketplaceReport

from st_aggrid import JsCode
import warnings 
warnings.filterwarnings('ignore')

st.set_page_config(layout="wide")
from styling import k_sep_formatter


if 'selected_client' not in st.session_state:
    st.session_state['selected_client'] = 'N/A'
if 'active' not in st.session_state:
    st.session_state['active'] = False

prev_loaded = False
NO_DECIMAL = Decimal(10) ** -0
THREE_DECIMAL = Decimal(10) ** -3


@st.experimental_memo
def fetch_client_config(config_manager,client,month,year):
    return config_manager.LoadConfig(client,month,year)

@st.experimental_memo
def fetch_lbms_data(client,month,year):
    return LBMSMonthlyData.Load(client,month,year)

@st.experimental_memo
def fetch_marketplace_data(month,year):
    return MarketplaceReport.Load(month,year)

@st.experimental_memo
def fetch_config_manager():
    config_manager = ClientConfigurationManager()
    config_manager.Init()
    return config_manager


def push_to_analytics(analytics,client,month,year):
    
    config_manager = fetch_config_manager()
    client_config = fetch_client_config(config_manager,client,month,year)

    for product in client_config.products:
        
        if product =="LBMS":
            try:
                lbms_data = fetch_lbms_data(client,month,year)
                # st.write(lbms_data)
                analytics.push_lbms_data(client_config,lbms_data)
            except:
                traceback.print_exc()
                lg.warning("LBMS Data Unavailable for :"+client+" - "+ str(month) + "/"+ str(year))
                
        if product =="Marketplace":
            try:
                #ack until marketplace data become available
                marketplace_data = fetch_marketplace_data(9,2022)
                marketplace_data.month=month
                marketplace_data.year=year
                analytics.push_marketplace_data(client_config,marketplace_data)
            except:
                lg.warning("Marketplace Data Unavailable for :"+str(month) + "/"+ str(year))

    


def dateFunc(s):
    toks = s.split("/")
    date = datetime.datetime(int(toks[1]),int(toks[0]),1)
    return date

def format_date(s):
    toks = s.split("/")
    return datetime.date(int(toks[1]),int(toks[0]),1).strftime('%B %Y')

def get_lbms_metrics(analytics,date,identifier):
    return analytics.GetMetrics(client, date,"Corporate Loyalty","LBMS",identifier)

def get_lbms_metrics_rel_perf(analytics,date_from,date_to,identifier):
    return analytics.GetMetricsRelativePerf(client, date_from,date_to,"Corporate Loyalty","LBMS",identifier)


def get_corp_loyalty_metrics(analytics,date,product,identifier):
    try:
        return analytics.GetMetrics(client, date,"Corporate Loyalty",product,identifier)
    except:
        return nan
    
def get_corp_loyalty_metrics_rel_perf(analytics,date_from,date_to,product,identifier):
    try:
        return analytics.GetMetricsRelativePerf(client, date_from,date_to,"Corporate Loyalty",product,identifier)
    except:
        return nan

def write_metric(analytics,elem, title, _format, multiplier, product, metric_id, date_from, date_to):
    elem.metric(title,_format.format(multiplier*get_corp_loyalty_metrics(analytics,date_to,product,metric_id)),
    '{:.2f}%'.format(get_corp_loyalty_metrics_rel_perf(analytics,date_from,date_to, product,metric_id)))

def client_updated(s):
    print("updated")

def add_line_trace(fig,df,row,col):
    fig.add_trace(
        go.Scatter(
            x=df["Date"],
            y=df["Value"],
            mode="lines"          
        ),row=row, col=col
    )



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
firstDate = list_of_dates[0]

df_client_map = GetClientMapDataFrame()
with st.sidebar:

    date_selected = st.sidebar.selectbox("Pick Date",list_of_dates, index = len(list_of_dates)-1, label_visibility="collapsed", format_func=format_date)
    toks = date_selected.split("/")
    st.session_state["month_selected"]=toks[0]
    st.session_state["year_selected"]=toks[1]
   
    gb = GridOptionsBuilder.from_dataframe(df_client_map)
    gb.configure_selection(selection_mode="single", use_checkbox=False, header_checkbox=False)
    gb.configure_column("Region",rowGroup=True,hide=True, rowGroupIndex= 0)
    gb.configure_column("Live",hide=True )
    gb.configure_column("Logo",hide=True)
    gb.configure_column("Name",hide=True)
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
        allow_unsafe_jscode=True,
        use_checkbox=False)
    v = response['selected_rows']
    if len(v)>0:
        if "Client" in v[0].keys():
            client_selected = v[0]["Client"]
            st.session_state["client_selected"] = client_selected
    
    if st.sidebar.button("Clear Cache"):
        st.experimental_memo.clear()
# No client selected yet
if  len(v)==0:
    st.markdown("#### Select a client ...")

elif not v[0]["Live"]:
    st.markdown("#### Reporting not live yet for "+ v[0]["Name"])

# Client is selected - run report script
if  len(v) and v[0]["Live"]>0:  

    monthlyReporting, overTime, tabExperimental, debug_tab = st.tabs(["Monthly Report", "Over Time", "Performance", "Debug"])
    
    with monthlyReporting:

        analytics = ClientsAnalytics()
        


        client = st.session_state["client_selected"]
        month = st.session_state["month_selected"]
        year = st.session_state["year_selected"]

        
        spot_client_config = fetch_client_config(fetch_config_manager(),client,month,year)
        spot_products = spot_client_config.products
        # Load Client Config and loop on products
        
        push_to_analytics(analytics,client,month,year)

        prev = GetPreviousMonth(int(st.session_state["month_selected"]),int(st.session_state["year_selected"]))
        prev_month = prev[0]
        prev_year = prev[1]

        push_to_analytics(analytics,client,prev_month,prev_year)

        spotDate = str(month)+"/"+str(year)
        prevDate = str(prev_month)+"/"+str(prev_year)
        
        # Name and Top line
        col1, col2,col3 = st.columns([1,2,1])
        net_top_line = 0
        try:
            image = Image.open('assets/'+v[0]["Logo"])
        except:
            image = Image.open('assets/Giift.png')
        col1.image(image, width=150)
        col2.header(v[0]["Name"])
        
        if "LBMS" in spot_products:
            net_top_line += get_lbms_metrics(analytics,spotDate,"net_revenues")
        if "LBMS" in spot_products:
            net_top_line += get_corp_loyalty_metrics(analytics,spotDate,"Marketplace","net_revenues")
        col3.metric("Total Monthly Net Revenue",'$ {:,.0f}'.format(net_top_line))
        
        # st.dataframe(analytics.main_frame)
        # AgGrid(analytics.main_frame)

        st.markdown("#### Key Performance Indicators")  
        col1, col2, col3,col4,col5 = st.columns(5)
        if "LBMS" in spot_products:
            col1.markdown(" ##### 🤝LBMS")
            write_metric(analytics,col5,"Take Rate",'{:.2f} bp',10000,"LBMS","take_rate",prevDate,spotDate)
            write_metric(analytics,col3,"Net Revenue / MAU",'$ {:.3f}',1,"LBMS","net_revenue_per_active_user",prevDate,spotDate)
            write_metric(analytics,col4,"Accrual Engagement Rate",'{:.1f}%',100,"LBMS","accrual_engagement_rate",prevDate,spotDate)
            write_metric(analytics,col2,"Net Revenues","$ {:,.0f}",1,"LBMS","net_revenues",prevDate,spotDate)
        
        col1, col2, col3,col4,col5 = st.columns(5)
        if "Marketplace" in spot_products:
            col1.markdown(" ##### 🛍️Marketplace")
            write_metric(analytics,col2,"Net Revenues","$ {:,.0f}",1,"Marketplace","net_revenues",prevDate,spotDate)
            write_metric(analytics,col3,"Transactions GMV",' $ {:,.0f}k',Decimal(0.001),"Marketplace","transactions_gmv",prevDate,spotDate)
            write_metric(analytics,col4,"Margins Rate",' {:.2f}%',100,"Marketplace","margins_rate",prevDate,spotDate)
            write_metric(analytics,col5,"Markups Rate",' {:.2f}%',100,"Marketplace","markups_rate",prevDate,spotDate)

        col1, col2, col3,col4,col5 = st.columns(5)
        if "GiiftBox" in spot_products:
            col1.markdown(" ##### 🎁GiiftBox")
            write_metric(analytics,col2,"Take Rate",'{:.2f} bp',10000,"LBMS","take_rate",prevDate,spotDate)
            write_metric(analytics,col3,"Net Revenue / MAU",'$ {:.3f}',1,"LBMS","net_revenue_per_active_user",prevDate,spotDate)

            
        # st.markdown("""---""")
        st.markdown("#### Product Metrics")
        if "LBMS" in spot_products:
            with st.expander("LBMS Metrics"):
                col1, col2, col3 = st.columns(3) 
                write_metric(analytics,col1,"Total Points Value ","$ {:,.0f}k",Decimal(0.001),"LBMS","total_points_std_usd",prevDate,spotDate)
                write_metric(analytics,col2,"Total Users", "{:,.0f}k",Decimal(0.001),"LBMS","total_users",prevDate,spotDate)
                write_metric(analytics,col3,"Monthly Active Users (MAU)", "{:,.0f}k",Decimal(0.001),"LBMS","accrual_active_users",prevDate,spotDate)  
                col1, col2, col3 = st.columns(3)
                write_metric(analytics,col1,"Points Accrued Value", "$ {:,.0f}",1,"LBMS","points_accrued_std_usd",prevDate,spotDate)
                write_metric(analytics,col2,"Points Redeemed Value", "$ {:,.0f}",1,"LBMS","points_redeemed_std_usd",prevDate,spotDate)
                write_metric(analytics,col3,"Accrual GMV", "$ {:,.0f}M",Decimal(0.000001),"LBMS","accrual_gmv",prevDate,spotDate)
        
        if "Marketplace" in spot_products:
            with st.expander("Marketplace Metrics"):
                col1, col2, col3 = st.columns(3)
                write_metric(analytics,col1,"Transactions Count",'{:,.0f}',1,"Marketplace","transactions_count",prevDate,spotDate)
                


        st.markdown("""---""")
        
        st.markdown("#### 💵Revenues")
        rev_df = analytics.revenue_frame[analytics.revenue_frame["Date"]==spotDate]

        with st.expander("Client Revenues"):
            # AgGrid(rev_df)
            st.markdown("""---""")
            col1, col2, = st.columns(2) 
            col1.metric("Gross Revenues","$ {:,.0f}".format(get_lbms_metrics(analytics,spotDate,"gross_revenues")))
            col2.metric("Net Revenues", "$ {:,.0f}".format(get_lbms_metrics(analytics,spotDate,"net_revenues")))
            # st.markdown("""---""")
            net_rev_df= rev_df[rev_df['Net Amount ($)'] != 0]
            net_rev_df = net_rev_df[["Business Line","Product","Revenue Type","Net Amount ($)", "Label"]]
            
            gb = GridOptionsBuilder.from_dataframe(net_rev_df)
            gb.configure_default_column(enablePivot=True, enableValue=True, enableRowGroup=True)
            gb.configure_side_bar()
            gb.configure_column("Client",hide=True)
            gb.configure_column("Date",hide=True)
            gb.configure_column("Business Line",rowGroup=True,hide=True, rowGroupIndex= 0)
            gb.configure_column("Product",rowGroup=True,hide=True, rowGroupIndex= 1)
            gb.configure_column("Revenue Type",rowGroup=True,hide=True, rowGroupIndex= 1)
            gb.configure_column("Net Amount ($)", aggFunc="sum",type=["numericColumn"], precision=0,valueFormatter=k_sep_formatter)
            # gb.configure_column("Points Accrued ($)", aggFunc="sum",type=["numericColumn"], precision=0,valueFormatter=k_sep_formatter)
            # gb.configure_column("Points Expired ($)", aggFunc="sum",type=["numericColumn"], precision=0,valueFormatter=k_sep_formatter)
            gridoptions = gb.build()
            response = AgGrid(
                net_rev_df,
                gridOptions=gridoptions,
                height=250,
                enable_enterprise_modules=True,
                update_mode=GridUpdateMode.NO_UPDATE,
                fit_columns_on_grid_load=True,
                header_checkbox_selection_filtered_only=True,
                allow_unsafe_jscode=True
                )
            
            fig1 = px.bar(net_rev_df, color="Revenue Type", x="Product",
             y="Net Amount ($)",
             title="Revenues Per Product and Type",
             barmode='group',
             height=400,
             width=500,
             hover_data=["Label","Net Amount ($)"],
      
            )

            fig2 = px.sunburst(net_rev_df[["Business Line","Product","Revenue Type", "Net Amount ($)"]], path=['Product', 'Revenue Type'], values="Net Amount ($)",
            color="Product", hover_data=["Net Amount ($)"],height=400,width=500,title="Products & Revenue Type Net Revenues")
           
            col1, col2 = st.columns(2)
            col1.plotly_chart(fig1)
            col2.plotly_chart(fig2)    
        st.markdown("""---""")
        st.markdown("#### :arrow_heading_up:Accruals")

        # AgGrid(caa.lbms_accruals)
        df_acc = analytics.lbms_accruals[analytics.lbms_accruals["Date"]==spotDate]
        
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
            color="Channel", hover_data=["Points Accrued ($)"],height=400,width=500,title="Channels & Products Accruals")
            col1.plotly_chart(fig)
            fig2 = px.scatter(df_acc[["Channel","Points Accrued ($)", "GMV ($)"]], x="Points Accrued ($)", y="GMV ($)", color="Channel",height=400,width=500,title="Channels & Products Accruals")
            col2.plotly_chart(fig2)

        # st.markdown("""---""")
        st.subheader("	:arrow_heading_down:Redemptions")

        df_red = analytics.lbms_redemptions[analytics.lbms_redemptions["Date"]==spotDate]
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
            fig1 = px.bar(df_red, x="Redemption Option", y="Points Redeemed ($)", color="Redemption Option", title="Redemptions by Option",height=400,
             width=500)
            fig1.update_layout(barmode='relative')
            col1.plotly_chart(fig1)  
            fig2 = px.scatter(df_red[["Redemption Option","Points Redeemed ($)","Average Transaction ($)", "Number Transactions"]], 
            x="Number Transactions", y="Average Transaction ($)", color="Redemption Option",height=400,width=500,title="Value / Number Transaction Scatter Plot" )
            col2.plotly_chart(fig2)

        # st.markdown("""---""")
        st.subheader(":family:Points Cohort Analytics")
        df_up = analytics.lbms_users_points[analytics.lbms_users_points["Date"]==spotDate]
        df_up["Average Points ($) in Cohort"]= df_up["Points Value ($)"] / df_up["Number Users"]
        df_up["Points Value ($)"]= df_up["Points Value ($)"].apply(lambda x: x.quantize(NO_DECIMAL))
        df_up["Average Points ($) in Cohort"]= df_up["Average Points ($) in Cohort"].apply(lambda x: x.quantize(THREE_DECIMAL))
        df_up = df_up.sort_values(["Average Points ($) in Cohort"], ascending=[False])
        # df_up.sort_index('Average Points ($) in Cohort')
        with st.expander("Points Cohort Data"):
            
            gb = GridOptionsBuilder.from_dataframe(df_up)
            gb.configure_default_column(enablePivot=True, enableValue=True, enableRowGroup=True)
            gb.configure_side_bar()
            gb.configure_column("Average Points ($) in Cohort",aggFunc="sum",type=["numericColumn"], precision=0,valueFormatter=k_sep_formatter)
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
            fig2 = px.scatter(df_up[["Average Points ($) in Cohort","Number Users","Points Value ($)"]], x="Average Points ($) in Cohort", y="Number Users"
            ,title="Cohort Points Scatter Plot")
            st.plotly_chart(fig2)


        

    with overTime:

        load_history = st.button("Load History")
        if load_history:
            analytics = ClientsAnalytics()

            for date in list_of_dates:
                tok = date.split("/")
                push_to_analytics(analytics,client,tok[0],tok[1])



            st.markdown("##### 🩺Health Indicators")
            # AgGrid(analytics.main_frame)
            with st.expander("Time Series Charts"):

                df_net_revenues= analytics.main_frame[analytics.main_frame["Identifier"]=="net_revenues"]      
                df_net_revenue_per_active_user= analytics.main_frame[analytics.main_frame["Identifier"]=="net_revenue_per_active_user"]
                df_take_rate= analytics.main_frame[analytics.main_frame["Identifier"]=="take_rate"]
                df_take_rate["Value"] = df_take_rate["Value"] *10000
                df_accrual_engagement_rate= analytics.main_frame[analytics.main_frame["Identifier"]=="accrual_engagement_rate"]
                df_accrual_engagement_rate["Value"] = df_accrual_engagement_rate["Value"] *100
                df_accrued= analytics.main_frame[analytics.main_frame["Identifier"]=="points_accrued_std_usd"]
                df_redeemed= analytics.main_frame[analytics.main_frame["Identifier"]=="points_redeemed_std_usd"]

                fig = make_subplots(
                    rows=2, cols=2,
                    shared_xaxes=True,
                    x_title='Dates',
                    vertical_spacing=0.07,
                    subplot_titles=[("Net Revenues ($)"),("Net Revenue per MAU ($)"),("Take Rate (bp)"),("Accruals Engagement Rate (%)")]
                )

                add_line_trace(fig,df_net_revenues,1,1)
                add_line_trace(fig,df_take_rate,2,1)
                add_line_trace(fig,df_net_revenue_per_active_user,1,2)
                add_line_trace(fig,df_accrual_engagement_rate,2,2)

                fig.update_layout(height=500, width=800,showlegend=False )
                
                st.plotly_chart(fig)

        

            

            st.markdown("##### :computer:  Key Account Metrics")

            with st.expander("Time Series Charts"):

                df_accrued= analytics.main_frame[analytics.main_frame["Identifier"]=="points_accrued"]
                df_redeemed= analytics.main_frame[analytics.main_frame["Identifier"]=="points_redeemed"]
                df_total_points = analytics.main_frame[analytics.main_frame["Identifier"]=="total_points"]
                df_total_users = analytics.main_frame[analytics.main_frame["Identifier"]=="total_users"]
                df_accrual_gmv = analytics.main_frame[analytics.main_frame["Identifier"]=="accrual_gmv"]
                df_active_users = analytics.main_frame[analytics.main_frame["Identifier"]=="accrual_active_users"]
                
                fig = make_subplots(
                    rows=2, cols=3,
                    shared_xaxes=True,
                    x_title='Dates',
                    vertical_spacing=0.07,
                    subplot_titles=["GMV ($)","Points Accrual ($)","Points Redemption ($)","Total Points Value ($)", "Total Users", "Monthly Active Users"]
                )

                add_line_trace(fig,df_accrual_gmv,1,1)
                add_line_trace(fig,df_accrued,1,2)
                add_line_trace(fig,df_redeemed,1,3)
                add_line_trace(fig,df_total_points,2,1)
                add_line_trace(fig,df_total_users,2,2)
                add_line_trace(fig,df_active_users,2,3)

                fig.update_layout(height=500, width=800,showlegend=False )
                
                st.plotly_chart(fig)

    with debug_tab:

        st.write(analytics)
    