
import streamlit as st

import os

import styling



# import sys
# sys.path.append("dra_common/")



os.environ["AWS_ACCESS_KEY_ID"] = st.secrets["key"]
os.environ["AWS_SECRET_ACCESS_KEY"] = st.secrets["secret"]
os.environ["AWS_DEFAULT_REGION"] = st.secrets["region"]

