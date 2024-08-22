import streamlit as st
import pandas as pd

def run():
    st.title("System Manual List")
    st.write("전산 시스템 사용 중 발생하는 궁금증을 해결해드립니다. 필요한 매뉴얼을 선택하여 확인해주세요 :bulb:")
    
    # 수직 간격을 줄이기 위해 hr 스타일 변경
    st.markdown(
        """
        <style>
        .custom-hr {
            border: 1.5px solid #e0f5ff;
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
        '키워드': ['키워드입니다.'] * 10,
        '문제': [
            '문제 확인필요.',
            '데이터 오류.',
            '서버 연결 실패.',
            '사용자 입력 오류.',
            '인증 오류.',
            '네트워크 문제.',
            'API 호출 오류.',
            '페이지 로드 실패.',
            '시간 초과.',
            '메모리 부족.'
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

    df['생성 날짜'] = pd.to_datetime(df['생성 날짜'], format='%Y.%m.%d')

    # 헤더 행에 대한 필터
    st.markdown("<div style='margin-bottom: 10px;'></div>", unsafe_allow_html=True)  # 추가된 간격
    col4, col5, col6, col7 = st.columns(4)

    with col4:
        period_filter = st.date_input("기간", key="period_filter_1", value=None)  # 고유한 키 사용
    with col5:
        category_filter = st.selectbox("카테고리", options=["전체"] + list(df['카테고리'].unique()), key="category_filter_1")  # 고유한 키 사용
    with col6:
        keyword_filter = st.selectbox("키워드", options=["전체"] + list(df['키워드'].unique()), key="keyword_filter_1")  # 고유한 키 사용
    with col7:
        issue_filter = st.text_input("문제 검색", value="", placeholder="문제를 검색하세요", key="issue_filter_1")  # 고유한 키 사용

    # 필터 조건 확인
    has_filters = any([
        period_filter is not None,
        category_filter != "전체",
        keyword_filter != "전체",
        issue_filter != ""
    ])

    # 데이터에 존재하는 값 목록
    valid_dates = df['생성 날짜'].dt.date.tolist()
    valid_categories = df['카테고리'].unique().tolist()
    valid_keywords = df['키워드'].unique().tolist()
    valid_issues = df['문제'].tolist()

    # 유효성 검사
    invalid_input = False
    if period_filter and period_filter not in valid_dates:
        invalid_input = True
    if category_filter != "전체" and category_filter not in valid_categories:
        invalid_input = True
    if keyword_filter != "전체" and keyword_filter not in valid_keywords:
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
    if keyword_filter != "전체":
        filtered_df = filtered_df[filtered_df['키워드'] == keyword_filter]
    if issue_filter:
        filtered_df = filtered_df[filtered_df['문제'].str.contains(issue_filter, case=False, na=False)]

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
