

import yaml
from yaml import SafeLoader

import streamlit as st
import streamlit_authenticator as stauth


def Auth():

    # if 'authentication_status' not in st.session_state:
    #     st.session_state['authentication_status'] = 'N/A'
    # if 'name' not in st.session_state:
    #     st.session_state['name'] = 'N/A'
    with open('./config.yaml') as file:
        config = yaml.load(file, Loader=SafeLoader)

    authenticator = stauth.Authenticate(
        config['credentials'],
        config['cookie']['name'],
        config['cookie']['key'],
        config['cookie']['expiry_days'],
        config['preauthorized']
    )


    name, authentication_status, username = authenticator.login('Login', 'sidebar')

    if authentication_status:
        authenticator.logout('Logout', 'sidebar')
        st.sidebar.write(f'Logged in as *{name}*')
        
        
        
    elif authentication_status == False:
        st.error('Username/password is incorrect')
    elif authentication_status == None:
        st.warning('Please enter your username and password')

