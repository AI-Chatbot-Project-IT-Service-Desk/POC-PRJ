import streamlit as st
import pandas as pd
from datetime import datetime

def run():
    st.title("미응답 데이터 관리")
    st.write("사용자 질의 중 응답하지 못한 내용에 관한 내역입니다.")
    
    # 수직 간격을 줄이기 위해 hr 스타일 변경
    st.markdown(
        """
        <style>
        .custom-hr {
            border: 1.5px solid #E0F7FA;
            margin-top: 10px;  /* 간격 조절 */
            margin-bottom: 10px;  /* 간격 조절 */
        }
        </style>
        <hr class="custom-hr">
        """,
        unsafe_allow_html=True
    )

    # 테이블을 위한 샘플 데이터
    sample_data = {
        '생성 날짜': ['2024.08.01', 
                    '2024.08.02',
                    '2024.08.03',
                    '2024.08.04',
                    '2024.08.05',
                    '2024.08.06',
                    '2024.08.07',
                    '2024.08.08',
                    '2024.08.09',
                    '2024.08.10'],
        '미응답 ID': ['cesco119'] * 10,
         '사용자 질문': [
            ['질문 내용입니다.'] * 10,
        ],
        '처리 상태',
    }

    # 사전을 DataFrame으로 변환
    df = pd.DataFrame(sample_data)
    
    # 사이드바 배경색 및 버튼 스타일 변경을 위한 커스텀 CSS 추가
    st.markdown(
        """
        <style>
        [data-testid="stSidebar"] {
            background-color:#e0f5ff; /* 연한 파란색 */
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
        """,
        unsafe_allow_html=True
    )

    # 버튼을 오른쪽으로 정렬
    col1, col2, col3 = st.columns([3, 1, 1])  # 버튼을 오른쪽으로 밀기 위해 컬럼 너비 조정
    with col1:
        st.write("")  # 버튼을 오른쪽으로 밀기 위한 빈 칸
    with col2:
        st.write("")  # 버튼을 오른쪽으로 밀기 위한 빈 칸
    with col3:
        data_download_button = st.button("데이터 다운로드", key="data_download")
        st.markdown('<div id="data_download_button"></div>', unsafe_allow_html=True)

    df['생성 날짜'] = pd.to_datetime(df['생성 날짜'], format='%Y.%m.%d')

    # 헤더 행에 대한 필터
    st.markdown("<div style='margin-bottom: 10px;'></div>", unsafe_allow_html=True)  # 추가된 간격
    col4, col5, col6 = st.columns(3)

    with col4:
        period_filter = st.date_input("기간", key="period_filter_1", value=None) 
    with col5:
        id_filter = st.text_input("미응답 ID", value="", placeholder="미응답 ID를 검색하세요", key="id_filter_1")
    with col6:
        question_filter = st.text_input("파일명", value="", placeholder="질문 내용을 검색하세요", key="question_filter_1")  

    # 필터 조건 확인
    has_filters = any([
        period_filter is not None,
        id_filter != "전체",
        question_filter != ""
    ])

    # 데이터에 존재하는 값 목록
    valid_dates = df['생성 날짜'].dt.date.tolist()
    valid_id = df['미응답 ID'].unique().tolist()
    valid_question = df['질문'].tolist()

    # 유효성 검사
    invalid_input = False
    if period_filter and period_filter not in valid_dates:
        invalid_input = True
    if id_filter != "전체" and id_filter not in valid_id:
        invalid_input = True
    if question_filter and not any(question_filter.lower() in issue.lower() for question in valid_question):
        invalid_input = True

    if invalid_input and has_filters:
        st.error("입력한 값을 다시 확인해주세요.")
        return

    # 필터 적용
    filtered_df = df.copy()  # 필터링 전 전체 데이터를 기본으로 표시

    if period_filter:
        filtered_df = filtered_df[filtered_df['생성 날짜'].dt.date == period_filter]
    if id_filter != "전체":
        filtered_df = filtered_df[filtered_df['미응답 ID'] == id_filter]
    if question_filter:
        filtered_df = filtered_df[filtered_df['질문'].str.contains(question_filter, case=False, na=False)]

    # DataFrame이 비어 있으면 전체 데이터 표시
    if filtered_df.empty:
        filtered_df = df

    # DataFrame을 HTML로 변환
    html = filtered_df.to_html(escape=False, index=False, formatters={
        '상세보기': lambda x: f'<a href="{x}" target="_blank" class="custom-button">링크</a>'
    })

    # HTML 테이블 표시
    st.markdown(f'<div class="centered-table-container"><div class="centered-table">{html}</div></div>', unsafe_allow_html=True)

    # 선택된 행의 세부 정보 표시
    if 'current_url' in st.session_state:
        st.markdown(f"[링크 열기]({st.session_state.current_url})")
        del st.session_state.current_url

# 실행
run()
