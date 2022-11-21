import streamlit as st
import streamlit_authenticator as stauth

hashed_passwords = stauth.Hasher(['@giift#3659#', '@giift#3659#']).generate()

print(hashed_passwords)