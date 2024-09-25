import os
import json
from PyPDF2 import PdfReader, PdfWriter
import io
import boto3
from botocore.exceptions import ClientError

# S3 설정 경로
s3_configure_path = './config/cesco-poc-os-service-key-1.txt'

# S3 설정 파일 읽기
with open(os.path.abspath(os.path.join(os.getcwd(), s3_configure_path))) as f:
    os_env_c = json.load(f)
    aws_access_key_id = os_env_c['access_key_id']
    aws_secret_access_key = os_env_c['secret_access_key']
    aws_region = os_env_c['region']
    bucket_name = os_env_c['bucket']
        
# S3 클라이언트 생성
s3_client = boto3.client(
    's3',
    aws_access_key_id=aws_access_key_id,
    aws_secret_access_key=aws_secret_access_key,
    region_name=aws_region
)

# 업로드할 경로
aws_pdf_path = 'cesco_division_file2'

print("[START] SAP Object Store S3 Connect Success")

#[20240911 강진욱] binary/octet-stream 형식으로 올라가 생기는 문제를 mime type 변경으로 해결하기 위해 application/pdf 지정 
def object_store_upload(uploaded_file, filecode, cesco_division_folder_path):
    # 원본 파일 업로드
    try:
        uploaded_file.seek(0)
        s3_client.upload_fileobj(
            uploaded_file,
            bucket_name,
            f"{aws_pdf_path}/{filecode}.pdf",
            ExtraArgs={
                'ContentType': 'application/pdf',
                'ContentDisposition': 'inline',
                'ACL': 'public-read'
            }
        )
        #print(f"[SUCCESS] {filecode}.pdf를 S3 버킷에 업로드하였습니다.")
    except ClientError as e:
        print(f"파일을 업로드 하는 도중 에러가 발생하였습니다.: {e}")

    # 자식 파일 업로드
    for division_file in os.listdir(cesco_division_folder_path):
        full_path = os.path.join(cesco_division_folder_path, division_file)
        try:
            with open(full_path, 'rb') as file:
                s3_client.upload_fileobj(
                    file,
                    bucket_name,
                    f"{aws_pdf_path}/{division_file}",
                    ExtraArgs={
                        'ContentType': 'application/pdf',
                        'ContentDisposition': 'inline',
                        'ACL': 'public-read'
                    }
                )
            #print(f"[SUCCESS] {division_file}를 S3 버킷에 업로드하였습니다.")
        except ClientError as e:
            print(f"파일을 업로드 하는 도중 에러가 발생하였습니다.: {e}")

    print("[SUCCESS] S3 Object Store Upload를 완료하였습니다")

#[20240911 강태영] os s3 host url 주소 return 
def getUrl() -> str:
    s3_host_url = "https://" + os_env_c['bucket'] + '.' + os_env_c['host'] + '/' + aws_pdf_path + '/'
    return s3_host_url

def getResources() -> str:
    s3_res_url = "https://" + os_env_c['bucket'] + '.' + os_env_c['host'] + '/resources/'
    return s3_res_url

#[20240911 강태영] s3 bucket에서 특정 파일 삭제):
def delete_file_from_s3(delete_file_list):
    for file in delete_file_list:
        try:
            s3_client.delete_object(
                Bucket=bucket_name,
                Key=f"{aws_pdf_path}/{file}"
            )
        except ClientError as e:
            print(f"[ERROR] 파일을 삭제하는 도중 에러가 발생하였습니다.: {e}")
    
    print("[SUCCESS] S3 Object Store Delete를 완료하였습니다")