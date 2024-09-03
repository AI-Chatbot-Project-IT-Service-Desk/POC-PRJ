import streamlit as st
from menu import menu_with_redirect
import pandas as pd
from datetime import datetime
import os
import sys

# Redirect to app.py if not logged in, otherwise show the navigation menu
menu_with_redirect()

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'server'))

from server import object_store_service as oss
from server import hana_cloud_service as hcs
from server import pdf_split as ps

def run():
    st.title("원본 데이터 관리")
    st.write("전산 시스템 사용 매뉴얼의 원본 데이터 입니다 📋")

    # 수직 간격을 줄이기 위해 hr 스타일 변경
    st.markdown(
        """
        <style>
        .custom-hr {
            border: 1.5px solid #E0F7FA;
            margin-top: 10px;  /* 간격 조절 */
            margin-bottom: 10px;  /* 간격 조절 */
        }
        .centered-table-container {
            display: flex;
            justify-content: center;
            margin-top: 20px;
        }
        .centered-table td, .centered-table th {
            text-align: center; /* 가운데 정렬 */
            padding: 10px; /* 여백 */
        }
        .centered-table th {
            background-color: #707070; /* 헤더 배경색 */
            color: #FFFFFF; /* 흰색 폰트 */
        }
        </style>
        <hr class="custom-hr">
        """,
        unsafe_allow_html=True
    )

    # 샘플 데이터
    sample_data = {
        '생성 날짜': ['2024.08.01', '2024.08.02', '2024.08.03', '2024.08.04', '2024.08.05',
                    '2024.08.06', '2024.08.07', '2024.08.08', '2024.08.09', '2024.08.10'],
        '카테고리': ['PDF', '세스넷', '세스넷', '기타 프로그램', '세스톡', '프린터', '세스넷', '기타 프로그램', '세스톡', '세스넷'],
        '파일명': ['Cesco_1', 'Cesco_2', 'Cesco_3', 'Cesco_4', 'Cesco_5', 'Cesco_6', 'Cesco_7', 'Cesco_8', 'Cesco_9', 'Cesco_10'],
        '상세보기': ['https://drive.google.com/file/d/1bO1HBNDKKV3ghPIHttG9rR-qjNqbQl1O/view?usp=sharing'] * 10,
    }

    # 딕셔너리를 DataFrame으로 변환
    df = pd.DataFrame(sample_data)
    df['생성 날짜'] = pd.to_datetime(df['생성 날짜'], format='%Y.%m.%d')

    # 세션 상태에서 선택된 행 추적
    if 'selected_rows' not in st.session_state:
        st.session_state.selected_rows = set()

    # 필터 추가
    col1, col2, col3 = st.columns([2, 2, 2])
    with col1:
        period_filter = st.date_input("기간", key="period_filter_1", value=None)
    with col2:
        category_filter = st.selectbox("카테고리", options=["전체"] + list(df['카테고리'].unique()), key="category_filter_1")
    with col3:
        issue_filter = st.text_input("파일명", value="", placeholder="파일명을 검색하세요", key="issue_filter_1")

    # 데이터 필터링
    filtered_df = df.copy()
    if period_filter:
        filtered_df = filtered_df[filtered_df['생성 날짜'].dt.date == period_filter]
    if category_filter != "전체":
        filtered_df = filtered_df[filtered_df['카테고리'] == category_filter]
    if issue_filter:
        filtered_df = filtered_df[filtered_df['파일명'].str.contains(issue_filter, case=False, na=False)]

    # 삭제 버튼
    col0, _, _, col4 = st.columns([1, 1, 3, 1])
    with col4:
        delete_button = st.button("삭제", key="delete_button_1")
        if delete_button:
            # 삭제할 인덱스 추출 및 삭제
            selected_indices = sorted(st.session_state.selected_rows)
            df = df.drop(index=selected_indices)
            st.session_state.selected_rows.clear()

    # 전체 선택 체크박스
    with col0:
        select_all = st.checkbox("전체 선택", value=len(st.session_state.selected_rows) == len(filtered_df))
        if select_all:
            st.session_state.selected_rows = set(filtered_df.index)
        else:
            st.session_state.selected_rows.clear()

    # 데이터프레임에 체크박스 추가
    for i, row in filtered_df.iterrows():
        col1, col2, col3, col4 = st.columns([1, 3, 4, 2])
        with col1:
            checkbox_key = f"select_{i}"
            # 체크박스에 label_visibility를 사용하여 레이블을 숨깁니다.
            checkbox = st.checkbox("Select", key=checkbox_key, value=i in st.session_state.selected_rows, label_visibility="collapsed")
            if checkbox:
                st.session_state.selected_rows.add(i)
            else:
                st.session_state.selected_rows.discard(i)
        with col2:
            st.write(row['생성 날짜'].strftime('%Y.%m.%d'))
        with col3:
            st.write(row['파일명'])
        with col4:
            st.write(f'<a href="{row["상세보기"]}" target="_blank" class="custom-button">링크</a>', unsafe_allow_html=True)

    # 선택된 항목 리스트 반환
    selected_items = [filtered_df.loc[i].to_dict() for i in st.session_state.selected_rows if i in filtered_df.index]

    st.write("선택된 항목들 (리스트):")
    st.json(selected_items)  # 리스트를 JSON 형식으로 출력

    # 업데이트된 데이터프레임 표시
    st.write("업데이트된 데이터 프레임:")
    st.dataframe(filtered_df)

    return selected_items  # 선택된 항목 리스트를 반환

# 실행
selected_items = run()
st.write("선택된 항목들 (반환된 리스트):")
st.json(selected_items)  # 반환된 리스트를 출력
