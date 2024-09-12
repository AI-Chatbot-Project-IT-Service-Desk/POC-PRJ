import streamlit as st
import base64
import os 
import json
from object_store import ObjectStore
from PyPDF2 import PdfReader, PdfWriter
import io

# Get configuration
s3_configure_path = './config/cesco-poc-os-service-key-1.txt'

with open(os.path.join(os.getcwd(), s3_configure_path)) as f:
    os_env_c = json.load(f)
    aws_access_key_id = os_env_c['access_key_id']
    aws_secret_access_key = os_env_c['secret_access_key']
    aws_region = os_env_c['region']
    aws_url = os.path.join('s3://', os_env_c['bucket'])

storage_options = {
    "aws_access_key_id": aws_access_key_id, 
    "aws_secret_access_key": aws_secret_access_key,
    "aws_region": aws_region
}

store = ObjectStore(aws_url, storage_options)

#aws_pdf_path = os.path.join(aws_url, 'test_cesco')
aws_pdf_path = os.path.join(aws_url+'/', 'cesco_division_file')
store = ObjectStore(aws_pdf_path, storage_options)

pdf_byte_data = store.get('cesco1.pdf')

pdf_stream = io.BytesIO(pdf_byte_data)
pdf_reader = PdfReader(pdf_stream)
pdf_writer = PdfWriter()

for page in pdf_reader.pages:
    pdf_writer.add_page(page)

pdf_output_stream = io.BytesIO()
pdf_writer.write(pdf_output_stream)
pdf_output_stream.seek(0)

base64_pdf = base64.b64encode(pdf_output_stream.read()).decode('utf-8')
print(base64_pdf)

href = f'<a href="data:application/pdf;base64,{base64_pdf}" target="_blank" style="display:inline-block; padding: 8px 16px; background-color:#0A84FF; color:white; text-align:center; text-decoration:none; border-radius:4px; font-size:16px;">새창에서 파일 열기</a>'
    
st.markdown(href, unsafe_allow_html=True)
st.markdown(f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="700" height="900" type="application/pdf"></iframe>', unsafe_allow_html=True)

href = f'<a href="data:application/pdf;base64,{base64_pdf}" target="_blank">문서보기</a>'
st.markdown(href, unsafe_allow_html=True)

st.link_button(label="메뉴얼 보기",
               url=f"data:application/pdf;base64,{base64_pdf}")