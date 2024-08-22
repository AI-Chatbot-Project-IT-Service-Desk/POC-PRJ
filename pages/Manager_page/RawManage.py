import streamlit as st
import pandas as pd
from datetime import datetime

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
        '카테고리': ['카테고리입니다.'] * 10,
         '파일명': [
            'Cesco_1',
            'Cesco_2',
            'Cesco_3',
            'Cesco_4',
            'Cesco_5',
            'Cesco_6',
            'Cesco_7',
            'Cesco_8',
            'Cesco_9',
            'Cesco_10'
        ],
        '상세보기': ['https://drive.google.com/file/d/1bO1HBNDKKV3ghPIHttG9rR-qjNqbQl1O/view?usp=sharing'] * 10,  # 샘플 링크 추가
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
        if 'show_uploader' not in st.session_state:
            st.session_state.show_uploader = False  # 초기 상태는 False로 설정

        if st.button("데이터 업로드", key="upload"):
            st.session_state.show_uploader = not st.session_state.show_uploader  # 버튼 누를 때마다 상태를 반전

    with col3:
        download_button = st.button("양식 다운로드", key="download")
        st.markdown('<div id="download_button"></div>', unsafe_allow_html=True)

    # 파일 업로드 처리
    if st.session_state.show_uploader:
        uploaded_file = st.file_uploader("PDF 파일을 업로드하세요", type="pdf")
        if uploaded_file is not None:
            # 파일을 지정한 디렉토리에 저장 (uploaded_날짜_시간.pdf 형식으로 저장)
            with open(f"uploaded_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf", "wb") as f:
                f.write(uploaded_file.getbuffer())
            st.success(f"파일 업로드 성공: {uploaded_file.name}")

    df['생성 날짜'] = pd.to_datetime(df['생성 날짜'], format='%Y.%m.%d')

    # 헤더 행에 대한 필터
    st.markdown("<div style='margin-bottom: 10px;'></div>", unsafe_allow_html=True)  # 추가된 간격
    col4, col5, col6 = st.columns(3)

    with col4:
        period_filter = st.date_input("기간", key="period_filter_1", value=None)  # 고유한 키 사용
    with col5:
        category_filter = st.selectbox("카테고리", options=["전체"] + list(df['카테고리'].unique()), key="category_filter_1")  # 고유한 키 사용
    with col6:
        issue_filter = st.text_input("파일명", value="", placeholder="파일명을 검색하세요", key="issue_filter_1")  # 고유한 키 사용

    # 필터 조건 확인
    has_filters = any([
        period_filter is not None,
        category_filter != "전체",
        issue_filter != ""
    ])

    # 데이터에 존재하는 값 목록
    valid_dates = df['생성 날짜'].dt.date.tolist()
    valid_categories = df['카테고리'].unique().tolist()
    valid_issues = df['파일명'].tolist()

    # 유효성 검사
    invalid_input = False
    if period_filter and period_filter not in valid_dates:
        invalid_input = True
    if category_filter != "전체" and category_filter not in valid_categories:
        invalid_input = True
    if issue_filter and not any(issue_filter.lower() in issue.lower() for issue in valid_issues):
        invalid_input = True

    if invalid_input and has_filters:
        st.error("입력한 값을 다시 확인해주세요.")
        return

    # 필터 적용
    filtered_df = df.copy()  # 필터링 전 전체 데이터를 기본으로 표시

    if period_filter:
        filtered_df = filtered_df[filtered_df['생성 날짜'].dt.date == period_filter]
    if category_filter != "전체":
        filtered_df = filtered_df[filtered_df['카테고리'] == category_filter]
    if issue_filter:
        filtered_df = filtered_df[filtered_df['파일명'].str.contains(issue_filter, case=False, na=False)]

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
