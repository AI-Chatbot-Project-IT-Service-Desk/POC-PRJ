import streamlit as st
from menu import menu_with_redirect
import pandas as pd
<<<<<<< HEAD
from datetime import datetime
=======
>>>>>>> c01fd469836ceec0dfa05a3fdca41a2cb3900b26
import os
import sys

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'server'))
#print("경로 확인", os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'server'))

from server import object_store_service as oss
from server import hana_cloud_service as hcs
from server import pdf_split as ps
# Redirect to app.py if not logged in, otherwise show the navigation menu
menu_with_redirect()

<<<<<<< HEAD
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'server'))
#print("경로 확인", os.path.dirname(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'server')))
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
        /* 버튼 스타일 수정 */
        .stButton > button {
            width: 117%; /* 버튼 가로 너비를 100%로 설정 */
            padding: 10px;
            font-size: 16px;
            cursor: pointer;
            border: none;
            border-radius: 5px;
            background-color: #007BFF;
            color: white;
        }
        .stButton > button:hover {
            background-color: #0056b3;
        }
        .stButton > button:active {
            background-color: #004085;
            box-shadow: 0 5px #666;
            transform: translateY(4px);
        }
        .button-spacing {
            margin: 30px; /* 버튼 간 간격 추가 */
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    # 버튼을 오른쪽으로 정렬
    col1, col2, col3, col4 = st.columns([3, 1, 1, 1])  # 버튼을 오른쪽으로 밀기 위해 컬럼 너비 조정
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
    
    with col4:
        delete_button = st.button("삭제", key="delete")
        st.markdown('<div id="delete_button"></div>', unsafe_allow_html=True)

    # 파일 업로드 처리
    if st.session_state.show_uploader:
        uploaded_file = st.file_uploader("PDF 파일을 업로드하세요", type="pdf")

        if uploaded_file is not None:
            check_form = ps.check_form(uploaded_file)

            if(not check_form):
                st.warning("지정된 폼으로 작성된 파일이 아닙니다.", icon="⚠️")
            else:
                upload_file_name = (uploaded_file.name).split(".pdf")[0] #업로드한 파일 이름 (확장자 제거)
                progress_text = "💻Preparing to upload data..."
                my_bar = st.progress(0.0, text=progress_text)

                page_output_dir = "./data/cesco_division_file"
                os.makedirs(page_output_dir, exist_ok=True)
                my_bar.progress(0.1, text=progress_text)

                #Object Store S3 한글 미지원 이슈로 인한 파일 이름 코드화 
                filecode = hcs.update_FileNamesDB(upload_file_name)
                my_bar.progress(0.2, text=progress_text)

                #자식 PDF 파일 생성
                ps.repeat_split_pdf(uploaded_file, page_output_dir, filecode)
                my_bar.progress(0.3, text="📃Generating a child PDF from the original file...")

                #Upload Object Store S3
                oss.object_store_upload(uploaded_file, str(filecode), page_output_dir)
                my_bar.progress(0.4, text="📦Uploading a file to the Cloud storage...")

                #Upload할 DataFrame 생성
                extract_dataframe = ps.extreact_pdf_to_dataframe(page_output_dir)
                my_bar.progress(0.8, text="💽Creating a DataFrame...")

                #HANA CLOUD UPLOAD
                hcs.upload_dataframe_to_hanacloud(extract_dataframe)
                my_bar.progress(0.9, text="📤Uploading data to the Cloud storage...")

                #split된 pdf 파일 삭제
                ps.delete_division_file(page_output_dir)
                my_bar.progress(1.0, text="😊The file upload is almost complete. Please wait a moment.")

                my_bar.empty()            
                st.success(f"파일 업로드 성공: {uploaded_file.name}")
                st.empty()

    df['생성 날짜'] = pd.to_datetime(df['생성 날짜'], format='%Y.%m.%d')

    # 헤더 행에 대한 필터
    st.markdown("<div style='margin-bottom: 10px;'></div>", unsafe_allow_html=True)  # 추가된 간격
    col5, col6, col7 = st.columns(3)

    with col5:
        period_filter = st.date_input("기간", key="period_filter_1", value=None)  # 고유한 키 사용
    with col6:
        category_filter = st.selectbox("카테고리", options=["전체"] + list(df['카테고리'].unique()), key="category_filter_1")  # 고유한 키 사용
    with col7:
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
=======
st.title("매뉴얼 데이터 관리 페이지")

manual_df = hcs.select_all_problemsolutions_table()

st.dataframe(
    manual_df,
    hide_index = True
)
>>>>>>> c01fd469836ceec0dfa05a3fdca41a2cb3900b26
