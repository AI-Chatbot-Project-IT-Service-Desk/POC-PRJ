import streamlit as st
from menu import menu_with_redirect
import pandas as pd
import os
import sys
import io

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'server'))

from server import hana_cloud_service as hcs

# Redirect to app.py if not logged in, otherwise show the navigation menu
menu_with_redirect()

st.title("매뉴얼 열람 페이지")
original_pdf_df = hcs.select_all_filenames_table()

# DataFrame 이름 지정
original_pdf_df.columns = ["파일명", "생성날짜", "상세보기"]

# '생성날짜' 컬럼을 datetime 형식으로 변환
original_pdf_df['생성날짜'] = pd.to_datetime(original_pdf_df['생성날짜'], errors='coerce')

# 체크박스를 위한 열 추가 (첫 번째 열에 삽입)
original_pdf_df.insert(0, "선택", False)  # 선택이라는 체크박스 열을 첫 열로 추가

# 사용자 입력 필터
col1, col2 = st.columns(2)

with col1:
    period_filter = st.date_input("생성날짜", key="period_filter_1", value=None)  # 고유한 키 사용
with col2:
    category_filter = st.selectbox("카테고리", options=["전체"] + list(original_pdf_df['파일명'].unique()), key="category_filter_1")  # 고유한 키 사용

# 필터 조건 확인
has_filters = any([
    period_filter is not None,
    category_filter != "전체"
])

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
    st.error("선택하신 날짜의 문서가 존재하지 않습니다.")
else:
    # 필터 적용
    filtered_df = original_pdf_df.copy()  # 필터링 전 전체 데이터를 기본으로 표시

    if period_filter:
        filtered_df = filtered_df[filtered_df['생성날짜'].dt.date == period_filter]
    if category_filter != "전체":
        filtered_df = filtered_df[filtered_df['파일명'] == category_filter]
    
    # 페이지네이션을 위한 설정
    pagination = st.container()

    # 버튼 클릭 시 페이지 업데이트
    if 'current_page' not in st.session_state:
        st.session_state.current_page = 1
    
    top_menu = st.columns((3, 1, 1))
    
    with top_menu[2]:
        batch_size = st.selectbox("Page Size", options=[5, 10, 20, 30, 40, 50], key="batch_size")
    with top_menu[1]:
        total_pages = ((len(filtered_df) // batch_size) + (1 if len(filtered_df) % batch_size > 0 else 0))
        current_page = st.number_input("Page", min_value=1, max_value=total_pages, step=1, key="current_page")
    with top_menu[0]:
        st.markdown(f"Page **{st.session_state.current_page}** of **{total_pages}** ")

    # 데이터 페이지 나누기
    def split_frame(input_df, rows):
        return [input_df.iloc[i:i + rows] for i in range(0, len(input_df), rows)]
    
    pages = split_frame(filtered_df, batch_size)
    if total_pages > 0:
        # st.data_editor를 사용하여 체크박스를 포함한 데이터 표시
        edited_df = st.data_editor(
            pages[st.session_state.current_page - 1],
            column_config={
                "선택": st.column_config.CheckboxColumn(),  # 체크박스는 수정 가능
                "파일명": st.column_config.TextColumn(disabled=True),  # 수정 불가
                "생성날짜": st.column_config.DateColumn(disabled=True),  # 수정 불가
                "상세보기": st.column_config.TextColumn(disabled=True)  # 수정 불가
                },
            use_container_width=True,
            )
        
        # 체크박스를 선택한 항목만 다운로드 및 삭제 기능
        selected_rows = edited_df[edited_df['선택'] == True]

        # 버튼을 배치할 빈 컨테이너
        btn_container = st.container()
        with btn_container:
            # 빈 공간을 만들기 위한 두 개의 빈 열
            top_menu_empty = st.columns((3, 1))

            # 다운로드 링크 생성 함수
            with top_menu_empty[1]:
                def create_download_link(df, file_name):
                    buffer = io.StringIO()
                    df.to_csv(buffer, index=False)
                    buffer.seek(0)
                    return st.download_button(
                        label="매뉴얼 다운로드",
                        data=buffer.getvalue(),
                        file_name=file_name,
                        mime="text/csv",
                        disabled=df.empty  # 선택된 항목이 없을 경우 버튼 비활성화
                    )
                # '매뉴얼 다운로드' 버튼을 항상 표시
                create_download_link(selected_rows, "selected_data.csv")

    else:
        st.warning("해당 조건에 맞는 데이터가 없습니다.")

# 페이지가 새로고침 될 때
if 'reload' in st.session_state and st.session_state.reload:
    st.session_state.reload = False
    st.experimental_rerun()
