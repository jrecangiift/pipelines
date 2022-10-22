
import streamlit as st

import os

import styling
from PIL import Image
image = Image.open('assets/analytics_logical_architecture.png')


with st.expander("Logical Architecture"):

    st.image(image)


# import sys
# sys.path.append("dra_common/")



os.environ["AWS_ACCESS_KEY_ID"] = st.secrets["key"]
os.environ["AWS_SECRET_ACCESS_KEY"] = st.secrets["secret"]
os.environ["AWS_DEFAULT_REGION"] = st.secrets["region"]

