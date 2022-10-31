
import streamlit as st

st.title("🛠️ Admin")

import auth_protocol
auth_protocol.Auth()
if st.session_state["authentication_status"]:
    if st.button("Clear Cache"):
        st.experimental_memo.clear()