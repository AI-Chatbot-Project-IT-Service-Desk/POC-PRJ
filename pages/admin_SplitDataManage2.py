import streamlit as st
from menu import menu_with_redirect
import pandas as pd
import os
import sys
import io

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'server'))

from server import hana_cloud_service as hcs
from server import object_store_service as oss

# Redirect to app.py if not logged in, otherwise show the navigation menu
menu_with_redirect()

st.title("매뉴얼 데이터 관리 페이지")
split_pdf_df = hcs.select_all_problemsolutions_table()

split_pdf_df.columns = ["파일명", "문제명", "생성날짜", "매뉴얼링크"]

#[20240911 강태영] s3 link url 붙이기
split_pdf_df["매뉴얼링크"] = oss.getUrl() + split_pdf_df["매뉴얼링크"]

# '생성날짜' 컬럼을 datetime 형식으로 변환
split_pdf_df['생성날짜'] = pd.to_datetime(split_pdf_df['생성날짜'], errors='coerce')

#[20240911 강태영] 데이터 프레임에 데이터가 있는지 확인
if split_pdf_df.empty: 
    st.info("저장된 매뉴얼이 없습니다. 매뉴얼을 업로드 해주세요", icon="ℹ️")
else:
    # 사용자 입력 필터
    col1, col2 = st.columns(2)

    with col1:
        period_filter = st.date_input("생성날짜", key="period_filter_1", value=None)  # 고유한 키 사용
    with col2:
        category_filter = st.selectbox("카테고리", options=["전체"] + list(split_pdf_df['파일명'].unique()), key="category_filter_1")  # 고유한 키 사용

    # 필터 조건 확인
    has_filters = any([
        period_filter is not None,
        category_filter != "전체"
    ])

    # 유효성 검사 및 필터 적용
    invalid_input = False
    if period_filter:
        valid_dates = split_pdf_df['생성날짜'].dt.date.tolist()
        if period_filter not in valid_dates:
            invalid_input = True

    if category_filter != "전체":
        valid_categories = split_pdf_df['파일명'].unique().tolist()
        if category_filter not in valid_categories:
            invalid_input = True

    if invalid_input and has_filters:
        st.warning("선택하신 날짜의 문서가 존재하지 않습니다.", icon="⚠️")
    else:
        # 필터 적용
        filtered_df = split_pdf_df.copy()  # 필터링 전 전체 데이터를 기본으로 표시

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
                    "파일명": st.column_config.TextColumn(disabled=True),  # 수정 불가
                    "문제명": st.column_config.TextColumn(disabled=True), #수정 불가
                    "생성날짜": st.column_config.DateColumn(disabled=True),  # 수정 불가
                    "매뉴얼링크": st.column_config.LinkColumn("매뉴얼 링크", 
                                                        display_text="상세보기",
                                                        disabled=True)  # 수정 불가
                    },
                use_container_width=True,
                hide_index=True,
            )
            
            # 버튼을 배치할 빈 컨테이너
            btn_container = st.container()
            with btn_container:
                # 빈 공간을 만들기 위한 두 개의 빈 열
                top_menu_empty = st.columns((3, 3, 2, 1))

                # 다운로드 링크 생성 함수
                with top_menu_empty[2]:
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
        else:
            st.warning("해당 조건에 맞는 데이터가 없습니다.")

# 페이지가 새로고침 될 때
# if 'reload' in st.session_state and st.session_state.reload:
#     st.session_state.reload = False
#     st.experimental_rerun()
