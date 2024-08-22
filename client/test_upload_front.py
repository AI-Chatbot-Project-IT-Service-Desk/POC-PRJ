import streamlit as st
import os
import sys
from IPython.display import display

sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))
from server import object_store_service as oss
from server import hana_cloud_service as hcs
from server import pdf_split as ps

#print("경로 확인", os.path.dirname(os.path.abspath(os.path.dirname(__file__))))

def main():
    #pdf 파일 업로드
    uploaded_file = st.file_uploader('PDF 파일을 업로드 하세요', type="pdf")
    
    if uploaded_file is not None:

        check_form = ps.check_form(uploaded_file)
        
        if(not check_form):
            st.warning("지정된 폼으로 작성된 파일이 아닙니다.", icon="⚠️")
        else:
            upload_file_name = (uploaded_file.name).split(".pdf")[0] #업로드한 파일 이름 (확장자 제거)
            progress_text = "Data Uploading.. Please Wait"
            my_bar = st.progress(0.0, text=progress_text)

            page_output_dir = "../data/cesco_division_file"
            os.makedirs(page_output_dir, exist_ok=True)
            my_bar.progress(0.1, text=progress_text)

            #Object Store S3 한글 미지원 이슈로 인한 파일 이름 코드화 
            filecode = hcs.update_FileNamesDB(upload_file_name)
            my_bar.progress(0.2, text=progress_text)

            #자식 PDF 파일 생성
            ps.repeat_split_pdf(uploaded_file, page_output_dir, filecode)
            my_bar.progress(0.3, text=progress_text)

            #Upload Object Store S3
            oss.object_store_upload(uploaded_file, str(filecode), page_output_dir)
            my_bar.progress(0.4, text=progress_text)

            #Upload할 DataFrame 생성
            extract_dataframe = ps.extreact_pdf_to_dataframe(page_output_dir)
            my_bar.progress(0.8, text=progress_text)

            #HANA CLOUD UPLOAD
            hcs.upload_dataframe_to_hanacloud(extract_dataframe)
            my_bar.progress(0.9, text=progress_text)

            #split된 pdf 파일 삭제
            ps.delete_division_file(page_output_dir)
            my_bar.progress(1.0, text=progress_text)

            my_bar.empty()
        
if __name__ == "__main__":
    main()