import streamlit as st
from menu import menu_with_redirect
import pandas as pd
import os
import sys
import datetime

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
    .stColumn {
        display: flex;
        flex-direction: column-reverse;
    }
    </style>
    """, unsafe_allow_html=True)

def update_filters_file():
    st.session_state["period_filter_start"] = None
    st.session_state["period_filter_end"] = None
    if st.session_state["selected_category"] != "전체":
        filter_problem = st.session_state["origin_dataframe"].loc[st.session_state["origin_dataframe"]["파일명"] == st.session_state["selected_category"]]
        st.session_state["problem_list"] = list(filter_problem["문제명"])
        st.session_state["selected_problem"] = "전체"
        st.session_state["filter_dataframe"] = filter_problem
    else:
        st.session_state["problem_list"] = list(st.session_state["origin_dataframe"]["문제명"])
        st.session_state["selected_problem"] = "전체"
        st.session_state["filter_dataframe"] = st.session_state["origin_dataframe"]
        st.session_state["period_filter_start"] = None
        st.session_state["period_filter_end"] = None

def update_filters_problem():
    if st.session_state["selected_problem"] != "전체":   
        filter_file = st.session_state["origin_dataframe"].loc[st.session_state["origin_dataframe"]["문제명"] == st.session_state["selected_problem"]]
        st.session_state["selected_category"] = filter_file["파일명"].iloc[0]
        st.session_state["period_filter_start"] = filter_file["생성날짜"].iloc[0]
        st.session_state["period_filter_end"] = filter_file["생성날짜"].iloc[0]
        st.session_state["filter_dataframe"] = filter_file
    else:
        update_filters_file()
        st.session_state["period_filter_start"] = None
        st.session_state["period_filter_end"] = None

#[20241014 강태영] 생성날짜(시작) 생성날짜(끝) 생성
def update_filters_date(x):
    print(st.session_state["period_filter_start"], type(st.session_state["period_filter_start"]))
    print(st.session_state["period_filter_end"], type(st.session_state["period_filter_end"]))

    if st.session_state["selected_problem"] == "전체":
        if st.session_state["period_filter_start"] is not None and st.session_state["period_filter_end"] is not None: 
            if st.session_state["period_filter_start"] > st.session_state["period_filter_end"]: 
                st.session_state["period_filter_start"] = st.session_state["past_start_date"]
                st.session_state["period_filter_end"] = st.session_state["past_end_date"]
                st.toast("생성날짜의 시작은 생성날짜의 끝 날짜보다 클 수 없습니다.", icon="⚠️")
            else:
                if st.session_state["selected_category"] == "전체":
                    st.session_state["filter_dataframe"] = st.session_state["origin_dataframe"][(st.session_state["origin_dataframe"]["생성날짜"].dt.date >= st.session_state["period_filter_start"]) &
                                                        (st.session_state["origin_dataframe"]["생성날짜"].dt.date <= st.session_state["period_filter_end"])]
                else:
                    st.session_state["filter_dataframe"] = st.session_state["filter_dataframe"][(st.session_state["filter_dataframe"]["생성날짜"].dt.date >= st.session_state["period_filter_start"]) &
                                                        (st.session_state["filter_dataframe"]["생성날짜"].dt.date <= st.session_state["period_filter_end"])]
                
                st.session_state["past_start_date"] = st.session_state["period_filter_start"]
                st.session_state["past_end_date"] = st.session_state["period_filter_end"]
    
    if st.session_state["period_filter_start"] is None:
        if st.session_state["selected_problem"] == "전체":
            st.session_state["period_filter_end"] = None
            if st.session_state["selected_category"] == "전체":
                st.session_state["filter_dataframe"] = st.session_state["origin_dataframe"]
            else:
                st.session_state["filter_dataframe"] = st.session_state["origin_dataframe"].loc[st.session_state["origin_dataframe"]["파일명"] == st.session_state["selected_category"]]

def reset_filters():
    st.session_state["selected_problem"] = "전체"
    st.session_state["selected_category"] = "전체"
    st.session_state["period_filter_start"] = None
    st.session_state["period_filter_end"] = None
    st.session_state["filter_dataframe"] = st.session_state["origin_dataframe"]

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

if "origin_dataframe" not in st.session_state:
    st.session_state["origin_dataframe"] = split_pdf_df
    #print("메타몽", split_pdf_df)

if "filter_dataframe" not in st.session_state:
    st.session_state["filter_dataframe"] = st.session_state["origin_dataframe"]

if 'category_list' not in st.session_state:
    st.session_state["category_list"] = list(st.session_state["origin_dataframe"]["파일명"].unique())

if 'problem_list' not in st.session_state:
    #print(st.session_state["origin_dataframe"])
    print(st.session_state["origin_dataframe"]["문제명"])
    st.session_state["problem_list"] = list(st.session_state["origin_dataframe"]["문제명"].unique())

if 'past_start_date' not in st.session_state:
    st.session_state["past_start_date"] = None

if 'past_end_date' not in st.session_state:
    st.session_state["past_end_date"] = None

# UI 구성
with st.container():
    st.markdown('<h2 class="title">매뉴얼 데이터 관리 페이지</h2>', unsafe_allow_html=True)
    st.markdown('<hr class="divider">', unsafe_allow_html=True)

    if split_pdf_df.empty: 
        st.info("저장된 매뉴얼이 없습니다. 매뉴얼을 업로드 해주세요", icon="ℹ️")
    else:
        col1, col2, col3, col4, col5 = st.columns([2, 3, 2, 2, 1])

        with col1:
            selected_category = st.selectbox(
                "파일명",
                options=["전체"] + st.session_state["category_list"],
                index=0,
                key="selected_category",
                on_change=update_filters_file
            )
        
        with col2:
            selected_problem = st.selectbox(
                "문제명",
                options=["전체"] + st.session_state["problem_list"],
                index=0,
                key="selected_problem",
                on_change=update_filters_problem
            )
        
        with col3:
            period_filter = st.date_input(
                "생성날짜(시작)", 
                key="period_filter_start", 
                value=None,
                on_change = update_filters_date,
            )
        
        with col4:
            period_filter2 = st.date_input(
                "생성날짜(끝)", 
                key="period_filter_end", 
                value=None,
                on_change = update_filters_date,
            )
        
        with col5:
            reset_button = st.button(
                label=":material/refresh:",
                on_click = reset_filters
            )

        #filtered_df = filter_data(split_pdf_df.copy(), period_filter, selected_problem, selected_category)
        filtered_df = st.session_state["filter_dataframe"]

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