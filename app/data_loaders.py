import streamlit as st

from clients_analytics_manager import ClientConfigurationManager, ClientAnalyticsManager




@st.experimental_memo
def fetch_config_manager():
    config_manager = ClientConfigurationManager()
    config_manager.Init()
    return config_manager

@st.experimental_memo
def LoadAllAnalytics():
    manager = ClientAnalyticsManager()
    analytics = manager.LoadClientAnalytics(['4/2022','5/2022','6/2022','7/2022','8/2022','9/2022','10/2022'])
    return analytics

