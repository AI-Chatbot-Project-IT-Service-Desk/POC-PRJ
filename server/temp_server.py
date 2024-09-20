import streamlit as st
import fitz  # PyMuPDF
import os
import json
import pandas as pd
import hana_ml
from hana_ml import ConnectionContext
from hana_ml.dataframe import create_dataframe_from_pandas
from object_store import ObjectStore
from gen_ai_hub.proxy.native.openai import embeddings
import shutil

def object_store_upload(uploaded_file, filecode, cesco_division_folder_path):
    s3_configure_path = '../config/cesco-poc-os-service-key-1.txt'

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

    store = ObjectStore(aws_url, storage_options)
    print("stroe 경로 확인 1", store.list())

    aws_pdf_path = os.path.join(aws_url + '/', 'cesco_division_file')
    store = ObjectStore(aws_pdf_path, storage_options)
    
    print("store 경로 확인 2", store.list())

    #원본 파일 업로드
    if uploaded_file.closed:
        print('[LOG] 파일이 닫혀 있습니다.')
    else:
        print("[LOG] 부모 파일이 열려 있습니다.")
    
    try:
        uploaded_file.seek(0)
        store.put(f'{filecode}.pdf', uploaded_file.read())
    except Exception as e:
        print(f"파일을 초기화 하는 도중 에러가 발생하였습니다.: {e}")

    for division_file in os.listdir(cesco_division_folder_path):
        print(os.path.join(cesco_division_folder_path + '/', division_file))
        full_path = os.path.join(cesco_division_folder_path + '/', division_file)
        with open(full_path, 'rb') as file:
            pdf_bytes = file.read()

        store.put(f"{division_file}", pdf_bytes)
    
    print("[LOG] S3 Object Store Upload를 완료하였습니다")