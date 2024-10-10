import streamlit as st
from menu import menu_with_redirect
import pandas as pd
import os
import sys

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'server'))
#print("경로 확인", os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'server'))

from server import object_store_service as oss
from server import hana_cloud_service as hcs
from server import pdf_split as ps

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

with st.container():
    st.markdown('<h2 class="title">매뉴얼 업로드 페이지</h2>', unsafe_allow_html=True)
    st.markdown('<hr class="divider">', unsafe_allow_html=True)

uploaded_file = st.file_uploader("PDF 파일을 업로드하세요.", type="pdf")

if uploaded_file is not None:
    check_form = ps.check_form(uploaded_file)

    if(not check_form):
        st.warning("지정된 폼으로 작성된 파일이 아닙니다.", icon="⚠️")
    else:
        #upload_file_name = (uploaded_file.name).split(".pdf")[0] #업로드한 파일 이름 (확장자 제거)

        upload_category_name = ps.extract_file_category(uploaded_file)

        if hcs.is_aready_exist_pdf_file(upload_category_name):
            st.toast("동일한 파일이 이미 업로드되어 있습니다. 파일을 변경하려면 [원본 데이터 관리]에서 기존 파일을 삭제한 후 다시 업로드해주세요.",
                    icon="⚠️")
            st.warning("동일한 파일이 이미 업로드되어 있습니다. 파일을 변경하려면 [원본 데이터 관리]에서 기존 파일을 삭제한 후 다시 업로드해주세요.",
                    icon="⚠️")
        else:
            #[20240826 강태영]동일한 파일명을 가진 PDF 파일을 업로드할 경우 업로드 여부 재 확인
            progress_text = "💻Preparing to upload data..."
            my_bar = st.progress(0.0, text=progress_text)

            page_output_dir = "./data/cesco_division_file"
            os.makedirs(page_output_dir, exist_ok=True)
            my_bar.progress(0.1, text=progress_text)

            #[20240827 강태영] 원본 파일 카테고리 추가
            file_category = ps.extract_file_category(uploaded_file)

            #Object Store S3 한글 미지원 이슈로 인한 파일 이름 코드화(원본 데이터 저장)
            filecode = hcs.update_FileNamesDB(file_category)
            my_bar.progress(0.2, text=progress_text)
                        
            # #자식 PDF 파일 생성
            my_bar.progress(0.3, text="📃Generating a child PDF from the original file...")
            ps.repeat_split_pdf(uploaded_file, page_output_dir, filecode)

            # #Upload Object Store S3
            my_bar.progress(0.4, text="📦Uploading a file to the Cloud storage...")
            # print("[LOG] filecode type", type(filecode))
            # print("[LOG] filecode", filecode)
            oss.object_store_upload(uploaded_file, str(filecode), page_output_dir)

            # #Upload할 DataFrame 생성
            my_bar.progress(0.8, text="💽Creating a DataFrame...")
            extract_dataframe = ps.extreact_pdf_to_dataframe(page_output_dir)

            # #HANA CLOUD UPLOAD
            my_bar.progress(0.9, text="📤Uploading data to the Cloud storage...")
            hcs.upload_dataframe_to_hanacloud(extract_dataframe, filecode)

            # #Split된 pdf 파일 삭제
            my_bar.progress(1.0, text="😊The file upload is almost complete. Please wait a moment.")
            ps.delete_division_file(page_output_dir)

            my_bar.empty()            
            st.success(f"파일 업로드 성공: {uploaded_file.name}")
            st.empty()


# 업로드 후 원본 데이터 관리 페이지 변경해주기
df = hcs.select_all_filenames_table()
df = df.set_index("CodeID")
# DataFrame 이름 지정
df.columns = ["파일명", "생성날짜", "매뉴얼링크"]
#[20240911 강태영] s3 link url 붙이기
df["매뉴얼링크"] = oss.getUrl() + df["매뉴얼링크"]
# '생성날짜' 컬럼을 datetime 형식으로 변환
df["생성날짜"] = pd.to_datetime(df['생성날짜'], errors='coerce')

st.session_state.original_pdf_df = df