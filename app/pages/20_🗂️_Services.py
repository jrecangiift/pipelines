
import streamlit as st
import services_model
import revenue_model
import meta_data as md
from decimal import Decimal
import pandas as pd
from st_aggrid import AgGrid, GridUpdateMode, GridOptionsBuilder, DataReturnMode
st.set_page_config(layout="wide")
from styling import k_sep_formatter

st.title("🗂️ Services")

import auth_protocol
auth_protocol.Auth()

if 'services_loaded' not in st.session_state:
    st.session_state['services_loaded'] = False
if 'df_services' not in st.session_state:
    st.session_state['df_services'] = {}


if st.session_state["authentication_status"]:


    months = range(13)[1:]
    years = ['2022','2023','2024']

    newserv, existing = st.tabs(["Enter New Service", "Registry",])

    with newserv:
        obj_list = md.GetClientMapList()
        # obj_list.sort()
        client_names = [c['Client'] for c in obj_list]
        
        currencies = ["USD", "AED", "GBP", "EUR", "QAR"]

        with st.form(key='service_form', clear_on_submit=True):
            col1, col2 = st.columns(2)
            col1.selectbox("Business Line",revenue_model.BusinessLine.list(), key = "business")
            col2.selectbox("Service's Type",services_model.ServiceType.list(), key="type")
            
            col1, col2, col3 = st.columns([2,1,1])
            col1.selectbox(("Client"),client_names,  key="client")
            col2.selectbox("Month",months, key="month")
            col3.selectbox("Years",years, key="year")

            col1, col2,col3 = st.columns([2,1,1])
            col1.number_input("Amount", min_value=0.0, key="amount")
            col2.selectbox("Currency Code",currencies , key="currency")

            st.text_area("Service Description", key="label")

    
            submitted = st.form_submit_button("Submit")

            if submitted:
                service = services_model.ServiceRevenueDeclaration(
                    st.session_state["type"],
                    st.session_state["business"],
                    st.session_state["label"],
                    st.session_state["client"],
                    st.session_state["month"],
                    st.session_state["year"],
                    Decimal(str(st.session_state["amount"])),
                    st.session_state["currency"]
                )
                try:
                    service.Save()
                    st.success("Service has been saved")
                except:
                    st.error("Service could not be saved")
  
    with existing:


        col1, col2,col3,col4= st.columns([1,1,1,3])
        col1.selectbox("Month",months, key="select_month", label_visibility='collapsed')
        col2.selectbox("Years",years, key="select_year", label_visibility='collapsed')
        refresh_button = col3.button("Refresh")
        if refresh_button or st.session_state['services_loaded']:
            st.session_state['services_loaded']=True
            
            if refresh_button:
                
                st.session_state['df_services'] =  services_model.ServiceRevenueDeclaration.List(
                st.session_state['select_month'],
                st.session_state['select_year'])

 
            
            df_services = pd.DataFrame(st.session_state['df_services'])
            

            if len(df_services)==0:
                st.warning("No Services logged for this month")

            else:

                gb = GridOptionsBuilder.from_dataframe(df_services)
                gb.configure_selection(selection_mode="single", use_checkbox=True, header_checkbox=False)
                # gb.configure_column("type",rowGroup=True,hide=False, rowGroupIndex= 0)
                # gb.configure_column("month",rowGroup=True,hide=True, rowGroupIndex= 1)
                # gb.configure_column("Live",hide=True )
                # gb.configure_column("Logo",hide=True)
                gb.configure_column("uuid",hide=True)
                gridoptions = gb.build()
                
                response = AgGrid(
                    df_services,
                    gridOptions=gridoptions,
                    
                    enable_enterprise_modules=False,
                    update_mode=GridUpdateMode.SELECTION_CHANGED,
                    data_return_mode=DataReturnMode.FILTERED_AND_SORTED,
                    fit_columns_on_grid_load=True,
                    header_checkbox_selection_filtered_only=True,
                    allow_unsafe_jscode=True,
                    use_checkbox=True)
                
                v = response['selected_rows']
                if len(v)==1:
                    # st.write(v)
                    if st.button("Delete"):
                        resp = services_model.ServiceRevenueDeclaration.DeleteByUUID(v[0]['period'],v[0]['uuid'])
                        # st.write(resp)

                        st.session_state['services_loaded']=True
                        st.success("Service Entry deleted - please refresh")
                        

