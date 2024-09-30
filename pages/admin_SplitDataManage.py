import streamlit as st
from menu import menu_with_redirect
import pandas as pd
import os
import sys

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'server'))

from server import hana_cloud_service as hcs
from server import object_store_service as oss

# Redirect to app.py if not logged in, otherwise show the navigation menu
menu_with_redirect()

st.markdown(""" 
    <style>
    .title {
        margin-bottom: -40px;  /* 제목과 구분선 사이의 간격을 줄이기 */
    }
    .divider {
        margin-top: 20px;  /* 구분선 위쪽의 간격을 늘리기 */
        margin-bottom: 70px;  /* 구분선 아래쪽의 간격을 늘리기 */
    }
    .metrics {
        margin-top: 30px;  /* 메트릭과 구분선 사이의 간격을 늘리기 */
    }
    </style>
    """, unsafe_allow_html=True)

# 필터 상태를 초기화하는 함수
def reset_filters():
    st.session_state["selected_problem"] = "전체"
    st.session_state["selected_category"] = "전체"

# 필터를 동적으로 업데이트하는 함수
def update_filters():
    selected_problem = st.session_state["selected_problem"]
    selected_category = st.session_state["selected_category"]

    # 문제 선택 시 파일명 업데이트
    if selected_problem != "전체":
        st.session_state["category_options"] = ["전체"] + list(split_pdf_df[split_pdf_df['문제명'] == selected_problem]['파일명'].unique())
    else:
        st.session_state["category_options"] = ["전체"] + list(split_pdf_df['파일명'].unique())

    # 파일명 선택 시 문제 업데이트
    if selected_category != "전체":
        st.session_state["problem_options"] = ["전체"] + list(split_pdf_df[split_pdf_df['파일명'] == selected_category]['문제명'].unique())
    else:
        st.session_state["problem_options"] = ["전체"] + list(split_pdf_df['문제명'].unique())

# 데이터 필터링 함수
def filter_data(df, period_filter, selected_problem, selected_category):
    if period_filter:
        df = df[df['생성날짜'].dt.date == period_filter]

    if selected_problem != "전체":
        df = df[df['문제명'] == selected_problem]

    if selected_category != "전체":
        df = df[df['파일명'] == selected_category]

    return df

# 데이터 페이지 나누기 함수
def split_frame(input_df, rows):
    return [input_df.iloc[i:i + rows] for i in range(0, len(input_df), rows)]

# 초기 데이터 가져오기
split_pdf_df = hcs.select_all_problemsolutions_table()
split_pdf_df.columns = ["파일명", "문제명", "생성날짜", "매뉴얼링크"]

# S3 link url 붙이기
split_pdf_df["매뉴얼링크"] = oss.getUrl() + split_pdf_df["매뉴얼링크"]

# '생성날짜' 컬럼을 datetime 형식으로 변환
split_pdf_df['생성날짜'] = pd.to_datetime(split_pdf_df['생성날짜'], errors='coerce')

# 필터 옵션 초기 설정
if 'category_options' not in st.session_state:
    st.session_state["category_options"] = ["전체"] + list(split_pdf_df['파일명'].unique())

if 'problem_options' not in st.session_state:
    st.session_state["problem_options"] = ["전체"] + list(split_pdf_df['문제명'].unique())

# UI 구성
with st.container():
    st.markdown('<h2 class="title">매뉴얼 데이터 관리 페이지</h2>', unsafe_allow_html=True)
    st.markdown('<hr class="divider">', unsafe_allow_html=True)

    if split_pdf_df.empty: 
        st.info("저장된 매뉴얼이 없습니다. 매뉴얼을 업로드 해주세요", icon="ℹ️")
    else:
        col1, col2, col3 = st.columns([1, 2, 3])

        with col1:
            period_filter = st.date_input("생성날짜", key="period_filter_1", value=None)

        with col3:
            selected_problem = st.selectbox(
                "문제명",
                options=st.session_state["problem_options"],
                key="selected_problem",
                on_change=update_filters
            )

        with col2:
            selected_category = st.selectbox(
                "파일명",
                options=st.session_state["category_options"],
                key="selected_category",
                on_change=update_filters
            )

        filtered_df = filter_data(split_pdf_df.copy(), period_filter, selected_problem, selected_category)

        if filtered_df.empty:
            st.warning("선택하신 날짜의 데이터가 존재하지 않습니다.", icon="⚠️")
        else:
            # Page Size 설정
            top_menu = st.columns((3, 1, 1))
            with top_menu[2]:
                batch_size = st.selectbox("Page Size", options=["전체", 5, 10, 20, 30, 40, 50], key="batch_size")

            # 페이지 나누기 처리
            if batch_size != "전체":
                batch_size = int(batch_size)
                pages = split_frame(filtered_df, batch_size)
                total_pages = len(pages)  # 전체 페이지 수 계산
                current_page = top_menu[1].number_input("Page", min_value=1, max_value=total_pages, value=1, step=1, key="current_page") if total_pages > 0 else 1
                display_df = pages[current_page - 1]  # 현재 페이지 데이터 표시
            else:
                display_df = filtered_df  # 전체 데이터를 표시
                total_pages = 1  # 전체 페이지 수를 1로 설정
                current_page = 1  # 현재 페이지 리셋

            # 페이지 정보 표시
            with top_menu[0]:
                st.markdown(f"Page **{current_page}** of **{total_pages}** ")
                select_all_checkbox = st.checkbox("전체 선택", key="select_all")

            # st.data_editor를 사용하여 데이터 표시
            edited_df = st.data_editor(
                display_df,
                column_config={
                    "파일명": st.column_config.TextColumn(disabled=True),  # 수정 불가
                    "문제명": st.column_config.TextColumn(disabled=True),  # 수정 불가
                    "생성날짜": st.column_config.DateColumn(disabled=True),  # 수정 불가
                    "매뉴얼링크": st.column_config.LinkColumn("매뉴얼 링크", 
                                                                display_text="상세보기",
                                                                disabled=True)  # 수정 불가
                },
                use_container_width=True,
                hide_index=True,
            )