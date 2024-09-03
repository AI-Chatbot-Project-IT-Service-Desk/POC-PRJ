import streamlit as st
from menu import menu_with_redirect
import pandas as pd
import os
import sys

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'server'))
#print("경로 확인", os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'server'))

from server import object_store_service as oss
from server import hana_cloud_service as hcs
from server import pdf_split as ps

# Redirect to app.py if not logged in, otherwise show the navigation menu
menu_with_redirect()

st.title("매뉴얼 원본 데이터 관리 페이지")
original_pdf_df = hcs.select_all_filenames_table()

#dataframe 이름 지정
original_pdf_df.columns = ["파일명", "생성날짜", "저장파일명"]

#저장된 파일 다운로드 버튼
st.download_button(label="원본 파일 다운로드",
                    data="",
                    file_name="",
                    mime='application/octet-stream')

#dataframe에서 보여줄 때는 저장 파일명을 숨기고 보여준다.
df_visible = original_pdf_df.drop(columns=['저장파일명'])

event = st.dataframe(
    df_visible,
    column_config={
        "파일명" : st.column_config.Column(
            "파일명",
            width="medium",
        ),
        "생성날짜" : st.column_config.Column(
            "생성날짜",
            width="medium"
        )
    },
    hide_index = True,
    on_select = "rerun",
    selection_mode = ["multi-row"],
    key="origin_table"
)

selected_row = event.selection

for i in selected_row['rows']:
    print(original_pdf_df.iloc[i, 2])