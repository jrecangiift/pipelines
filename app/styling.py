import streamlit as st

from st_aggrid import JsCode



k_sep_formatter = JsCode("""
    function(params) {
        return (params.value == null) ? params.value : params.value.toLocaleString(); 
    }
    """)

# st.write("""
# <style>
# @import url('https://fonts.googleapis.com/css2?family=Montserrat');
# html, body, [class*="css"]  {
#    font-family: 'Montserrat', cursive;
# }
# </style>
# """, unsafe_allow_html=True)



# st.markdown("""
#     <style>
#             .css-18e3th9 {
#                 padding-top: 2rem;
#                 padding-bottom: 10rem;
#                 padding-left: 3rem;
#                 padding-right: 3rem;
#             }
#             .css-1d391kg {
#                 padding-top: 3.5rem;
#                 padding-right: 1rem;
#                 padding-bottom: 3.5rem;
#                 padding-left: 1rem;
#             }
#     </style>
#     """, unsafe_allow_html=True)

# def SetFancyMetrics():

#     st.markdown("""
#     <style>
#     div[data-testid="metric-container"] {
#     background-color: rgb(240,242,246);
#     border: 3px solid black;
#     padding: 4% 4% 4% 10%;
#     border-radius: 10px;
#     color: rgb(100, 100, 119);
#     overflow-wrap: break-word;
#     }

#     /* breakline for metric text         */
#     div[data-testid="metric-container"] > label[data-testid="stMetricLabel"] > div {
#     overflow-wrap: break-word;
#     white-space: break-spaces;
#     color: black;
#     }
#     </style>
#     """
#     , unsafe_allow_html=True)