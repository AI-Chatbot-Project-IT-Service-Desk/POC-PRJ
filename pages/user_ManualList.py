import streamlit as st
from menu import menu_with_redirect
import pandas as pd
import os
import sys
import io
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
    if st.session_state["selected_category_user"] != "전체":
        filter_problem = st.session_state["origin_dataframe_user"].loc[st.session_state["origin_dataframe_user"]["파일명"] == st.session_state["selected_category_user"]]
        st.session_state["filter_dataframe_user"] = filter_problem
        st.session_state["period_filter_start_user"] = filter_problem["생성날짜"].iloc[0]
        st.session_state["period_filter_end_user"] = filter_problem["생성날짜"].iloc[0]
    else:
        st.session_state["filter_dataframe_user"] = st.session_state["origin_dataframe_user"]
        st.session_state["period_filter_start_user"] = None
        st.session_state["period_filter_end_uesr"] = None

#[20241014 강태영] 생성날짜(시작) 생성날짜(끝) 생성
def update_filters_date():
    if st.session_state["selected_category_user"] == "전체":
        if st.session_state["period_filter_start_user"] is not None and st.session_state["period_filter_end_user"] is not None: 
            if st.session_state["period_filter_start_user"] > st.session_state["period_filter_end_user"]:
                st.session_state["period_filter_start_user"] = st.session_state["past_start_date_user"]
                st.session_state["period_filter_end_user"] = st.session_state["past_end_date_user"]
                st.toast("생성날짜의 시작은 생성날짜의 끝 날짜보다 클 수 없습니다.", icon="⚠️")
            else:
                st.session_state["filter_dataframe_user"] = st.session_state["origin_dataframe_user"][(st.session_state["origin_dataframe_user"]["생성날짜"].dt.date >= st.session_state["period_filter_start_user"]) &
                                                         (st.session_state["origin_dataframe_user"]["생성날짜"].dt.date <= st.session_state["period_filter_end_user"])]
                
            st.session_state["past_start_date_user"] = st.session_state["period_filter_start_user"]
            st.session_state["past_end_date_user"] = st.session_state["period_filter_end_user"] 
    
        if st.session_state["period_filter_start_user"] is None:
            st.session_state["period_filter_end_user"] = None
            st.session_state["filter_dataframe_user"] = st.session_state["origin_dataframe_user"]

# reset함수
def reset_filters():
    st.session_state["selected_category_user"] = "전체"
    st.session_state["period_filter_start_user"] = None
    st.session_state["period_filter_end_user"] = None
    st.session_state["filter_dataframe_user"] = st.session_state["origin_dataframe_user"]

# 데이터 페이지 나누기 함수
def split_frame(input_df, rows):
    return [input_df.iloc[i:i + rows] for i in range(0, len(input_df), rows)]

with st.container():
    st.markdown('<h2 class="title">매뉴얼 열람 페이지</h2>', unsafe_allow_html=True)
    st.markdown('<hr class="divider">', unsafe_allow_html=True)

data = hcs.select_all_filenames_table()
original_pdf_df = data.drop(columns="CodeID")

# DataFrame 이름 지정
original_pdf_df.columns = ["파일명", "생성날짜", "매뉴얼링크"]

# S3 link URL 붙이기
original_pdf_df["매뉴얼링크"] = oss.getUrl() + original_pdf_df["매뉴얼링크"]

# '생성날짜' 컬럼을 datetime 형식으로 변환
original_pdf_df['생성날짜'] = pd.to_datetime(original_pdf_df['생성날짜'], errors='coerce')

#filtered_df = original_pdf_df.copy()

if "origin_dataframe_user" not in st.session_state:
    st.session_state["origin_dataframe_user"] = original_pdf_df
    #print("메타몽", split_pdf_df)

if "filter_dataframe_user" not in st.session_state:
    st.session_state["filter_dataframe_user"] = st.session_state["origin_dataframe_user"]

if 'category_list_user' not in st.session_state:
    st.session_state["category_list_user"] = list(st.session_state["origin_dataframe_user"]["파일명"].unique())

if 'past_start_date_user' not in st.session_state:
    st.session_state["past_start_date_user"] = None

if 'past_end_date_user' not in st.session_state:
    st.session_state["past_end_date_user"] = None

if original_pdf_df.empty:
    st.info("저장된 매뉴얼이 없습니다. 매뉴얼을 업로드 해주세요", icon="ℹ️")
else:
    # 사용자 입력 필터
    col1, col2, col3, col4 = st.columns([4,2,2,1])

    with col1:
        category_filter = st.selectbox("파일명", 
                                       options=["전체"] + st.session_state["category_list_user"], 
                                       index=0,
                                       key="selected_category_user",
                                       on_change=update_filters_file)  # 고유한 키 사용

    with col2:
        period_filter = st.date_input(
            "생성날짜(시작)", 
            key="period_filter_start_user", 
            value=None,
            on_change = update_filters_date
            )  # 고유한 키 사용

    with col3:
        period_filter2 = st.date_input(
            "생성날짜(끝)", 
            key="period_filter_end_user", 
            value=None,
            on_change = update_filters_date
        )
    
    with col4:
        reset_button = st.button(
            label=":material/refresh:",
            on_click = reset_filters
        )

    # 필터 조건 확인
    # has_filters = any([
    #     period_filter is not None,
    #     category_filter != "전체"
    # ])

    # # 유효성 검사 및 필터 적용
    # invalid_input = False
    # if period_filter:
    #     valid_dates = original_pdf_df['생성날짜'].dt.date.tolist()
    #     if period_filter not in valid_dates:
    #         invalid_input = True

    # if category_filter != "전체":
    #     valid_categories = original_pdf_df['파일명'].unique().tolist()
    #     if category_filter not in valid_categories:
    #         invalid_input = True

    filtered_df = st.session_state["filter_dataframe_user"]

    if filtered_df.empty:
        st.warning("선택하신 날짜의 문서가 존재하지 않습니다.", icon="⚠️")
    else:
        # 필터링 적용
        # if period_filter:
        #     filtered_df = filtered_df[filtered_df['생성날짜'].dt.date == period_filter]

        # if category_filter != "전체":
        #     filtered_df = filtered_df[filtered_df['파일명'] == category_filter]

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

        if not display_df.empty:
            st.data_editor(
                display_df,
                column_config={
                    "선택": st.column_config.CheckboxColumn(),  # 체크박스는 수정 가능
                    "파일명": st.column_config.TextColumn(disabled=True),  # 수정 불가
                    "생성날짜": st.column_config.DateColumn(disabled=True),  # 수정 불가
                    "매뉴얼링크": st.column_config.LinkColumn("매뉴얼 링크", display_text="상세보기", disabled=True)  # 수정 불가
                },
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.warning("해당 조건에 맞는 데이터가 없습니다.")
