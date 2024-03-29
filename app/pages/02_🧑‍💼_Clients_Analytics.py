from cmath import log, nan
from curses import meta
import streamlit as st
import datetime
import sys
from decimal import Decimal
from utils import GetPreviousMonth
from meta_data import GetClientMapDataFrame
from st_aggrid import AgGrid, GridUpdateMode, GridOptionsBuilder, DataReturnMode
import plotly.express as px
import logging as lg
from PIL import Image
from fx_conversion import FXConverter
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import traceback


from data_loaders import fetch_config_manager, LoadAllAnalytics

from product_lbms_model import LBMSMonthlyData
from clients_analytics import ClientsAnalytics
from client_configuration_model import ClientConfigurationManager,ClientConfiguration
from product_marketplace_model import MarketplaceReport

from clients_analytics_manager import ClientAnalyticsManager
from streamlit_option_menu import option_menu
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
            x=df.index,
            y=df,
            mode="lines"          
        ),row=row, col=col
    )


st.title("🧑‍💼 Clients Analytics")


import auth_protocol
auth_protocol.Auth()
if st.session_state["authentication_status"]:


    ### Build the date list with x look_back
    now = datetime.datetime.today()
    lookback_in_months = 7

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
        # st.write("month "+st.session_state["month_selected"])
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
            use_checkbox=False,
            license_key=st.secrets["aggrid_license"])
        v = response['selected_rows']
        if len(v)>0:
            if "Client" in v[0].keys():
                client_selected = v[0]["Client"]
                st.session_state["client_selected"] = client_selected
        
        if st.sidebar.button("Clear Cache"):
            st.experimental_memo.clear()
    # No client selected yet


    if  len(v)==0 : 
        st.markdown("#### Select a client ...")
    
    elif 'Client' not in v[0]:
        st.markdown("#### Select a client ...")

    elif not v[0]["Live"]:
        st.markdown("#### Reporting not live yet for "+ v[0]["Name"])






    # Client is selected - run report script
    elif  len(v) and v[0]["Live"]>0:  

        menu_selection = option_menu(None, ["Monthly Report", "History", "Performance", 'Debug'], 
        icons=['file-earmark', 'graph-up', "clipboard-data", 'gear'], 
        menu_icon="cast", default_index=0, orientation="horizontal" )

        if menu_selection == 'Monthly Report':
            
            analytics = LoadAllAnalytics()
            client = st.session_state["client_selected"]            

              
            month = st.session_state["month_selected"]
            year = st.session_state["year_selected"]

            
            spot_client_config = fetch_client_config(fetch_config_manager(),client,month,year)
            spot_products = spot_client_config.products
            # Load Client Config and loop on products
            
            # push_to_analytics(analytics,client,month,year)

            prev = GetPreviousMonth(int(st.session_state["month_selected"]),int(st.session_state["year_selected"]))
            prev_month = prev[0]
            prev_year = prev[1]

            # push_to_analytics(analytics,client,prev_month,prev_year)

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
           
            gross_top_line = analytics.main_frame[(analytics.main_frame['Client']==client) &
            (analytics.main_frame['Date']==spotDate) & 
            (analytics.main_frame['Identifier']=="gross_revenues")]["Value"].sum()

            net_top_line= analytics.main_frame[(analytics.main_frame['Client']==client) &
            (analytics.main_frame['Date']==spotDate) & 
            (analytics.main_frame['Identifier']=="net_revenues")]["Value"].sum()
            col3.metric("Total Monthly Net Revenue",'$ {:,.0f}'.format(net_top_line))
            

            # sandbox for groupby


            # df_rev = analytics.revenue_frame[(analytics.revenue_frame['Client']==client) &
            # (analytics.revenue_frame['Date']==spotDate)].groupby(['Business Line'])['Net Amount ($)']
            # print(df_rev.sum())
            # st.write(df_rev.sum())
            # st.write(analytics.main_frame[(analytics.main_frame['Client']==client) &
            # (analytics.main_frame['Date']==spotDate)])

            # st.dataframe(analytics.main_frame)
            # AgGrid(analytics.main_frame)

            rev_df = analytics.revenue_frame[(analytics.revenue_frame["Date"]==spotDate) & (analytics.revenue_frame["Client"]==client)]

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

            col1, col2, col3,col4,col5 = st.columns(5)
            if "Services" in spot_products:
                col1.markdown(" ##### 👩‍💻Services")
                write_metric(analytics,col2,"Net Revenues","$ {:,.0f}",1,"Services","net_revenues",prevDate,spotDate)
                # Here we get data from revenue frame to display by type (PS / Marketing / Prop. Offers)
                rev_df_services = rev_df[(rev_df["Product"]=="Services")]
                col3.metric("Professional Services",
                    '$ {:,.0f}'.format(rev_df_services[(rev_df_services['Revenue Type']=="Professional Services")]["Net Amount ($)"].sum()))
                col4.metric("Marketing Services",
                    '$ {:,.0f}'.format(rev_df_services[(rev_df_services['Revenue Type']=="Marketing Services")]["Net Amount ($)"].sum()))
                col5.metric("Prop. Offers",
                    '$ {:,.0f}'.format(rev_df_services[(rev_df_services['Revenue Type']=="Prop. Offers")]["Net Amount ($)"].sum()))
            
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
            
            # AgGrid(rev_df)
            with st.expander("Client Revenues"):
                # AgGrid(rev_df)
                st.markdown("""---""")
                col1, col2, = st.columns(2) 
                col1.metric("Gross Revenues","$ {:,.0f}".format(gross_top_line))
                col2.metric("Net Revenues", "$ {:,.0f}".format(net_top_line))
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
                    allow_unsafe_jscode=True,
                    license_key=st.secrets["aggrid_license"]
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
            
            #### LBMS Product Reporting #####
            if "LBMS" in spot_products:
                st.markdown("""---""")
                st.subheader("🤝LBMS")
                
                st.markdown("##### :arrow_heading_up:Accruals")

                # AgGrid(caa.lbms_accruals)
                df_acc = analytics.lbms_accruals[(analytics.lbms_accruals["Date"]==spotDate) & (analytics.lbms_accruals["Client"]==client)]
                
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
                    gb.configure_column("Points Accrued", aggFunc="sum",type=["numericColumn"], precision=0,valueFormatter=k_sep_formatter)
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
                st.markdown("#####	:arrow_heading_down:Redemptions")

                df_red = analytics.lbms_redemptions[(analytics.lbms_redemptions["Date"]==spotDate) & (analytics.lbms_redemptions["Client"]==client)]
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
                        allow_unsafe_jscode=True,
                        license_key=st.secrets["aggrid_license"]
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
                st.markdown("##### :family:Points Cohort Analytics")

                try:

                    df_up = analytics.lbms_users_points[(analytics.lbms_users_points["Date"]==spotDate)&  (analytics.lbms_users_points["Client"]==client)]
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
                            allow_unsafe_jscode=True,
                            license_key=st.secrets["aggrid_license"]
                            )


                    with st.expander("Point Value Analytics Chart"):
                        fig2 = px.scatter(df_up[["Average Points ($) in Cohort","Number Users","Points Value ($)"]], x="Average Points ($) in Cohort", y="Number Users"
                        ,title="Cohort Points Scatter Plot")
                        st.plotly_chart(fig2)

                except:
                    st.warning("Points Cohort Analytics Unavailable for this client" )


            if "Marketplace" in spot_products:
                st.markdown("""---""")
                st.subheader("	🛍️ Marketplace")

                marketplace_code = spot_client_config.marketplace_configuration.marketplace_code
                # st.write(marketplace_code)
                st.markdown("##### ↪️ Margins")

                marg_frame = analytics.marketplace_margins
                marg_frame = marg_frame[(marg_frame["Client"]==marketplace_code)]

                AgGrid(marg_frame)

                st.markdown("#####	↩️ Markups")

                mark_frame = analytics.marketplace_markups_det
                mark_frame = mark_frame[(mark_frame["Client"]==marketplace_code)]

                AgGrid(mark_frame)

                

        elif menu_selection =='History':

            # load_history = st.button("Load History")
            # if load_history:
            #     analytics = ClientsAnalytics.Load()

            #     # for date in list_of_dates:
            #     #     tok = date.split("/")
            #     #     push_to_analytics(analytics,client,tok[0],tok[1])
            analytics = LoadAllAnalytics()
            client = st.session_state["client_selected"]  

            st.markdown("##### Key Performance Indicators")
            # AgGrid(analytics.main_frame)
            with st.expander("Time Series Charts"):



                net_revenues= analytics.main_frame[(analytics.main_frame["Identifier"]=="net_revenues")& (analytics.main_frame["Client"]==client)].groupby(['Date'])['Value'].sum()
                
                net_revenue_per_active_user= analytics.main_frame[(analytics.main_frame["Identifier"]=="net_revenue_per_active_user" )& (analytics.main_frame["Client"]==client)].groupby(['Date'])['Value'].sum()
                
                take_rate= 10000*analytics.main_frame[(analytics.main_frame["Identifier"]=="take_rate") & (analytics.main_frame["Client"]==client)].groupby(['Date'])['Value'].sum()
                # df_take_rate["Value"] = df_take_rate["Value"] *10000
                accrual_engagement_rate= 100* analytics.main_frame[(analytics.main_frame["Identifier"]=="accrual_engagement_rate")& (analytics.main_frame["Client"]==client)].groupby(['Date'])['Value'].sum()
                
                accrued= analytics.main_frame[(analytics.main_frame["Identifier"]=="points_accrued_std_usd")& (analytics.main_frame["Client"]==client)].groupby(['Date'])['Value'].sum()
                redeemed= analytics.main_frame[(analytics.main_frame["Identifier"]=="points_redeemed_std_usd")& (analytics.main_frame["Client"]==client)].groupby(['Date'])['Value'].sum()

                fig = make_subplots(
                    rows=2, cols=2,
                    shared_xaxes=True,
                    x_title='Dates',
                    vertical_spacing=0.07,
                    subplot_titles=[("Net Revenues ($)"),("Net Revenue per MAU ($)"),("Take Rate (bp)"),("Accruals Engagement Rate (%)")]
                )
                # st.write(df_agg_net.index)
                add_line_trace(fig,net_revenues,1,1)
            
            
                add_line_trace(fig,take_rate,2,1)
                add_line_trace(fig,net_revenue_per_active_user,1,2)
                add_line_trace(fig,accrual_engagement_rate,2,2)

                fig.update_layout(height=600, width=1200,showlegend=False )
                
                st.plotly_chart(fig)

        

            

            st.markdown("#####  Key Account Metrics")

            with st.expander("Time Series Charts"):

                df_accrued= analytics.main_frame[(analytics.main_frame["Identifier"]=="points_accrued_std_usd")& (analytics.main_frame["Client"]==client)].groupby(['Date'])['Value'].sum()
                df_redeemed= analytics.main_frame[(analytics.main_frame["Identifier"]=="points_redeemed_std_usd")& (analytics.main_frame["Client"]==client)].groupby(['Date'])['Value'].sum()
                df_total_points = analytics.main_frame[(analytics.main_frame["Identifier"]=="total_points_std_usd")& (analytics.main_frame["Client"]==client)].groupby(['Date'])['Value'].sum()
                df_total_users = analytics.main_frame[(analytics.main_frame["Identifier"]=="total_users")& (analytics.main_frame["Client"]==client)].groupby(['Date'])['Value'].sum()
                df_accrual_gmv = analytics.main_frame[(analytics.main_frame["Identifier"]=="accrual_gmv")& (analytics.main_frame["Client"]==client)].groupby(['Date'])['Value'].sum()
                df_active_users = analytics.main_frame[(analytics.main_frame["Identifier"]=="accrual_active_users")& (analytics.main_frame["Client"]==client)].groupby(['Date'])['Value'].sum()
                
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

                fig.update_layout(height=600, width=1200,showlegend=False )
                
                st.plotly_chart(fig)

        