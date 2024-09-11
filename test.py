import streamlit as st

# print("hello_test")

# link = '<a href="https://hcp-a8f3d857-56e7-4be2-a9d1-d558ccd5da72.s3-ap-northeast-1.amazonaws.com/test_cesco/test3.pdf" target="_blank">여기에서 PDF 보기</a>'
# st.markdown(link, unsafe_allow_html=True)

# # PDF 파일을 새 탭에서 여는 링크 생성 (S3 퍼블릭 링크 사용)
# pdf_link = "https://hcp-a8f3d857-56e7-4be2-a9d1-d558ccd5da72.s3-ap-northeast-1.amazonaws.com/test_cesco/test3.pdf"

# # 버튼 모양의 하이퍼링크 생성
# st.markdown(f'<a href="{pdf_link}" target="_blank"><button style="padding:10px 20px; background-color:#4CAF50; color:white; border:none; border-radius:5px;">PDF 보기</button></a>', unsafe_allow_html=True)


# PDF 파일의 S3 퍼블릭 링크
pdf_link = "https://hcp-a8f3d857-56e7-4be2-a9d1-d558ccd5da72.s3-ap-northeast-1.amazonaws.com/test_cesco/test3.pdf"

# iframe을 사용해 PDF를 직접 표시
st.markdown(f'<iframe src="{pdf_link}" width="700" height="1000"></iframe>', unsafe_allow_html=True)