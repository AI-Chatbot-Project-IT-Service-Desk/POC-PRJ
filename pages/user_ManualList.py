import streamlit as st
from menu import menu_with_redirect
import pandas as pd
import os
import sys

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'server'))

from server import object_store_service as oss
from server import hana_cloud_service as hcs
from server import pdf_split as ps

# Redirect to app.py if not logged in, otherwise show the navigation menu
menu_with_redirect()

st.title("매뉴얼 열람 페이지")

original_pdf_df = hcs.get_menual_data()
st.dataframe(original_pdf_df, height=1000)