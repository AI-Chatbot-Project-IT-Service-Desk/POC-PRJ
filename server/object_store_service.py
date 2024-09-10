'''
작성일: 2024-09-10
설명: object store s3 원본파일, split된 자식 파일 upload // 메타데이터 타입 변경
'''

import os
import json
import boto3
from botocore.exceptions import ClientError

def object_store_upload(uploaded_file, filecode, cesco_division_folder_path):
    # S3 설정 경로
    s3_configure_path = './config/s3-service-key-cesco1-interim.txt'

    # S3 설정 파일 읽기
    with open(os.path.join(os.getcwd(), s3_configure_path)) as f:
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
    aws_pdf_path = 'cesco_division_file'
    
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
        print(f"[SUCCESS] {filecode}.pdf를 S3 버킷에 업로드하였습니다.")
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
            print(f"[SUCCESS] {division_file}를 S3 버킷에 업로드하였습니다.")
        except ClientError as e:
            print(f"파일을 업로드 하는 도중 에러가 발생하였습니다.: {e}")

    print("[SUCCESS] S3 Object Store Upload를 완료하였습니다")