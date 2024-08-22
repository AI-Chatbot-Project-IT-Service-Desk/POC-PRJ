import streamlit as st
import pandas as pd

# 각 페이지를 함수로 정의
def raw_data_management():
    st.title("원본데이터 관리")
    show_qna_management_content()

def qna_data_management():
    st.title("QnA 데이터 관리")
    show_qna_management_content()

def noreply_data_management():
    st.title("미응답데이터 관리")
    st.write("Manage data for unanswered questions.")

# QnA 데이터 관리에서 사용되는 공통 콘텐츠 함수
def show_qna_management_content():
    # 샘플 데이터 생성
    sample_data = {
        '기간': ['2024.08.01'] * 10,
        '카테고리': ['카테고리입니다.'] * 10,
        '키워드': ['키워드입니다.'] * 10,
        '문제': ['문제 확인필요.'] * 10,
        '링크': ['http://example.com'] * 10,  # 샘플 링크 추가
    }

    # 데이터프레임으로 변환
    sample_df = pd.DataFrame(sample_data)

    # 사이드바 배경색 변경을 위한 CSS 추가
    st.markdown(
        """
        <style>
        [data-testid="stSidebar"] {
            background-color:#E0F7FA; /* 연한 파란색 */
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    # 버튼을 오른쪽으로 정렬
    col1, col2, col3, col4 = st.columns([5, 2, 2, 1])  # 버튼을 오른쪽으로 밀기 위해 컬럼 너비 조정
    with col1:
        st.write("")  # 버튼을 오른쪽으로 밀기 위한 빈 칸
    with col2:
        upload_button = st.button("데이터 업로드", key="upload")
        st.markdown('<div id="upload_button"></div>', unsafe_allow_html=True)
    with col3:
        download_button = st.button("양식 다운로드", key="download")
        st.markdown('<div id="download_button"></div>', unsafe_allow_html=True)
    with col4:
        delete_button = st.button("삭제", key="delete")
        st.markdown('<div id="delete_button"></div>', unsafe_allow_html=True)
    
    # 파일 업로드
    uploaded_file = st.file_uploader("xlsx 파일 업로드", type="xlsx")
    

    if uploaded_file:
        try:
        # Excel 파일을 읽을 때 엔진을 명시적으로 지정합니다.
            df = pd.read_excel(uploaded_file, engine='openpyxl')
        except ValueError as e:
            st.error("Excel 파일을 읽는 중 오류가 발생했습니다. 파일이 유효한 .xlsx 파일인지 확인하세요.")
            st.error(str(e))
    else:
        df = sample_df

    df['기간'] = pd.to_datetime(df['기간'], format='%Y.%m.%d')

    # 필터 헤더 행
    col4, col5, col6, col7, col8 = st.columns(5)

    with col4:
        period_filter = st.date_input("기간")
    with col5:
        category_filter = st.selectbox("카테고리", options=["전체"] + list(df['카테고리'].unique()))
    with col6:
        keyword_filter = st.selectbox("키워드", options=["전체"] + list(df['키워드'].unique()))
    with col7:
        issue_filter = st.selectbox("문제", options=["전체"] + list(df['문제'].unique()))
    with col8:
        st.write("상세보기")

    # 필터 적용
    filtered_df = df[
        ((df['기간'] == pd.to_datetime(period_filter)) if period_filter else True) &
        ((df['카테고리'] == category_filter) if category_filter != "전체" else True) &
        ((df['키워드'] == keyword_filter) if keyword_filter != "전체" else True) &
        ((df['문제'] == issue_filter) if issue_filter != "전체" else True)
    ]

    # 체크박스용 컬럼 추가
    filtered_df['선택'] = False

    # 전체 선택 체크박스
    select_all = st.checkbox("전체 선택", key="select_all")

    # 필터링된 데이터프레임을 체크박스 및 "상세보기" 버튼과 함께 표시
    for i, row in filtered_df.iterrows():
        cols = st.columns(len(filtered_df.columns))  # 각 행의 아이템별로 컬럼 생성 (체크박스 제외)
        selected = cols[0].checkbox(f"{i}", value=select_all or row['선택'], key=f"checkbox_{i}")
        filtered_df.at[i, '선택'] = selected  # 체크박스 값으로 데이터프레임 업데이트
        for col, value in zip(cols[1:], row[:-2]):  # 마지막 두 컬럼 (URL과 체크박스) 제외
            col.write(value)
        if cols[-1].button("상세보기", key=f"details_{i}"):
            st.session_state.current_url = row['링크']

    # 세션 상태에 따라 링크 표시
    if 'current_url' in st.session_state:
        st.markdown(f"[링크 열기]({st.session_state.current_url})")
        del st.session_state.current_url

    # 선택된 행의 세부 정보 표시
    selected_rows = filtered_df[filtered_df['선택']]
    if not selected_rows.empty:
        st.write("선택된 항목 세부 정보:")
        for _, row in selected_rows.iterrows():
            st.write(f"**행 {row.name}:**")
            st.write(row)
            st.markdown(f"[링크 열기]({row['링크']})")  # 링크 표시

    # 페이지 네비게이션 (페이지 숫자 조절)
    st.write("Page navigation")
    page = st.slider("Select page", 1, 16, 1)
    st.write(f"Current page: {page}")

    if not selected_rows.empty:
        st.write("선택된 항목 세부 정보:")
        for _, row in selected_rows.iterrows():
            st.write(f"**행 {row.name}:**")

# 사이드바 네비게이션
pages = {
    "원본데이터 관리": raw_data_management,
    "QnA 데이터 관리": qna_data_management,
    "미응답데이터 관리": noreply_data_management
}

st.sidebar.title("관리자 페이지")
page = st.sidebar.radio("선택", list(pages.keys()))

# 선택한 페이지에 해당하는 함수 호출
pages[page]()
