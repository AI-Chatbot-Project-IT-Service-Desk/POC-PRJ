import os
import json
from object_store import ObjectStore
from PyPDF2 import PdfReader, PdfWriter
import io

s3_configure_path = './config/s3-service-key-cesco1-interim.txt'

with open(os.path.join(os.getcwd(), s3_configure_path)) as f:
    os_env_c = json.load(f)
    aws_access_key_id = os_env_c['access_key_id']
    aws_secret_access_key = os_env_c['secret_access_key']
    aws_region = os_env_c['region']
        
    ### Update path 
    aws_url = os.path.join('s3://', os_env_c['bucket'])

storage_options = {
    "aws_access_key_id": aws_access_key_id, 
    "aws_secret_access_key": aws_secret_access_key,
    "aws_region": aws_region
}

aws_pdf_path = os.path.join(aws_url + '/', 'cesco_division_file')
store = ObjectStore(aws_pdf_path, storage_options)
    
#print("[store path]", store.list())

print("[START] SAP Object Store S3 Connect Success")

def object_store_upload(uploaded_file, filecode, cesco_division_folder_path):
    # s3_configure_path = './config/s3-service-key-cesco1-interim.txt'

    # with open(os.path.join(os.getcwd(), s3_configure_path)) as f:
    #     os_env_c = json.load(f)
    #     aws_access_key_id = os_env_c['access_key_id']
    #     aws_secret_access_key = os_env_c['secret_access_key']
    #     aws_region = os_env_c['region']
        
    #     ### Update path 
    #     aws_url = os.path.join('s3://', os_env_c['bucket'])

    # storage_options = {
    #     "aws_access_key_id": aws_access_key_id, 
    #     "aws_secret_access_key": aws_secret_access_key,
    #     "aws_region": aws_region
    # }

    #store = ObjectStore(aws_url, storage_options)
    #print("stroe 경로 확인 1", store.list())

    # aws_pdf_path = os.path.join(aws_url + '/', 'cesco_division_file')
    # store = ObjectStore(aws_pdf_path, storage_options)
    
    # print("[store path]", store.list())

    # if uploaded_file.closed:
    #     print('[LOG] 파일이 닫혀 있습니다.')
    # else:
    #     print("[LOG] 부모 파일이 열려 있습니다.")
    
    #원본 파일 업로드
    try:
        uploaded_file.seek(0)
        store.put(str(filecode) + '.pdf', uploaded_file.read())
    except Exception as e:
        print(f"파일을 초기화 하는 도중 에러가 발생하였습니다.: {e}")

    #자식 파일 업로드
    for division_file in os.listdir(cesco_division_folder_path):
        print(os.path.join(cesco_division_folder_path + '/', division_file))
        full_path = os.path.join(cesco_division_folder_path + '/', division_file)
        with open(full_path, 'rb') as file:
            pdf_bytes = file.read()

        store.put(str(division_file), pdf_bytes)
    
    print("[SUCCESS] S3 Object Store Upload를 완료하였습니다")

#[20240828 강태영] PDF 파일 저장 및 열기 
def open_pdf_file(file_code, file_name, type):
    #type [origin, split]

    print("[GET] PDF 파일", type)
    pdf_byte_data = store.get(file_code)

    # print(pdf_byte_data)
    # Create a bytes stream from the byte data
    pdf_stream = io.BytesIO(pdf_byte_data)
    pdf_reader = PdfReader(pdf_stream)
    pdf_writer = PdfWriter()

    # Add all pages from the reader to the writer
    for page in pdf_reader.pages:
        pdf_writer.add_page(page)
    
    #[20240903 강태영]
    #download_path는 카테고리 + 번호 조합으로 정한다
    if type == "split":
        extract_num = file_code.split(sep='_')[1]
        download_path = file_name + "_" + extract_num
    elif type == "origin":
        download_path = file_name+".pdf"
    
    print("download_path", download_path)

    with open(download_path, "wb") as f:
        pdf_writer.write(f)

    with open(download_path, "rb") as pdf_file:
        PDFbyte = pdf_file.read()
    
    result = {}

    result['data'] = PDFbyte
    result['file_name'] = download_path

    return result