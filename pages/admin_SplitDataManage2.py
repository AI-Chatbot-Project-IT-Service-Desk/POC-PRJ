import streamlit as st
from menu import menu_with_redirect
import pandas as pd
from datetime import datetime
import os
import sys

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'server'))
#print("경로 확인", os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'server'))

from server import object_store_service as oss
from server import hana_cloud_service as hcs
from server import pdf_split as ps
# Redirect to app.py if not logged in, otherwise show the navigation menu
menu_with_redirect()

st.title("매뉴얼 데이터 관리")
st.write("전산 시스템 사용 매뉴얼 데이터 입니다.📋")

menual_data = hcs.get_menual_data()
st.dataframe(menual_data)