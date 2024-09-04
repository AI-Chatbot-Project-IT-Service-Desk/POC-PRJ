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

st.title("매뉴얼 원본 데이터 관리 페이지")
original_pdf_df = hcs.select_all_filenames_table()

# DataFrame 이름 지정
original_pdf_df.columns = ["파일명", "생성날짜", "저장파일명"]

# 사용자 입력 필터
col1, col2 = st.columns(2)

with col1:
    period_filter = st.date_input("기간", key="period_filter_1", value=None)  # 고유한 키 사용
with col2:
    category_filter = st.selectbox("카테고리", options=["전체"] + list(original_pdf_df['파일명'].unique()), key="category_filter_1")  # 고유한 키 사용

# Initialize session state for selected files
if 'selected_files' not in st.session_state:
    st.session_state.selected_files = []

<<<<<<< HEAD
# 필터 조건 확인
has_filters = any([
    period_filter is not None,
    category_filter != "전체"
])
=======
selected_row = event.selection
>>>>>>> 4954a7d8bf97eaee329e48466c65bf42f13dbf6d

# 유효성 검사 및 필터 적용
invalid_input = False
if period_filter:
    valid_dates = original_pdf_df['생성날짜'].dt.date.tolist()
    if period_filter not in valid_dates:
        invalid_input = True

if category_filter != "전체":
    valid_categories = original_pdf_df['파일명'].unique().tolist()
    if category_filter not in valid_categories:
        invalid_input = True

if invalid_input and has_filters:
    st.error("입력한 값을 다시 확인해주세요.")
else:
    # 필터 적용
    filtered_df = original_pdf_df.copy()  # 필터링 전 전체 데이터를 기본으로 표시

    if period_filter:
        filtered_df = filtered_df[filtered_df['생성날짜'].dt.date == period_filter]
    if category_filter != "전체":
        filtered_df = filtered_df[filtered_df['파일명'] == category_filter]
    
    # DataFrame이 비어 있으면 전체 데이터 표시
    if filtered_df.empty:
        filtered_df = original_pdf_df

    # 각 행에 대한 버튼 추가
    for idx, row in filtered_df.iterrows():
        col1, col2, col3 = st.columns([2, 2, 1])
        with col1:
            st.write(row['파일명'])
        with col2:
            st.write(row['생성날짜'])
        with col3:
            if st.button("매뉴얼 확인", key=f"button_{idx}"):
                # Reset the selected_files list and add the current file info
                st.session_state.selected_files = [{
                    "파일명": row['파일명'],
                    "생성날짜": row['생성날짜']
                }]

    # 선택된 파일 리스트 표시
    if st.session_state.selected_files:
        st.write("선택된 파일들:")
        st.write(st.session_state.selected_files)

    # 선택된 파일 리스트를 반환
    selected_files_list = st.session_state.selected_files
