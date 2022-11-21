
import streamlit as st

import os
import yaml
from yaml import SafeLoader
import styling
from PIL import Image
from streamlit_option_menu import option_menu
import boto3
import streamlit as st
st.set_page_config(layout="wide")
from styling import k_sep_formatter

# if 'authentication_status' not in st.session_state:
#     st.session_state['authentication_status'] = None
# if 'name' not in st.session_state:
#     st.session_state['name'] = None

st.title("🏠 Welcome")
import auth_protocol
auth_protocol.Auth()

selected2 = option_menu(None, ["How-to", "Upload", "Tasks", 'Settings'], 
    icons=['house', 'cloud-upload', "list-task", 'gear'], 
    menu_icon="cast", default_index=0, orientation="horizontal" )
selected2

# import sys
# sys.path.append("dra_common/")




# os.environ["AWS_ACCESS_KEY_ID"] = st.secrets["key"]
# print(os.environ["AWS_ACCESS_KEY_ID"])
# st.write(os.environ["AWS_ACCESS_KEY_ID"])
# os.environ["AWS_SECRET_ACCESS_KEY"] = st.secrets["secret"]
# os.environ["AWS_DEFAULT_REGION"] = st.secrets["region"]



if st.session_state["authentication_status"]:

    s3 = boto3.resource('s3')
    # print(boto3.DEFAULT_SESSION.get_credentials().access_key)    
    # st.write(boto3.DEFAULT_SESSION.get_credentials().access_key)   
    # print(os.environ["aws_access_key_id"])
    # st.write(os.environ["aws_access_key_id"])

    image = Image.open('assets/analytics_logical_architecture.png')
    with st.expander("Logical Architecture"):

        st.image(image)