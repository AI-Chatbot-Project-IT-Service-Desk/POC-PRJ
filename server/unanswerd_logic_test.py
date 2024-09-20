'''
작성일: 2024-08-21
설명: 무응답 로직 테스트 파일
'''
import os
import json
import pandas as pd
import hana_ml
from hana_ml import ConnectionContext
from hana_ml.dataframe import create_dataframe_from_pandas
from gen_ai_hub.proxy.native.openai import embeddings

# CESCO_UNANSWEREDQUESTIONS Table Select 함수
def get_unanswerd_questions_data():
    with open(os.path.join(os.getcwd(), './config/cesco-poc-hc-service-key.json')) as f:
        hana_env_c = json.load(f)
        port_c = hana_env_c['port']
        user_c = hana_env_c['user']
        host_c = hana_env_c['host']
        pwd_c = hana_env_c['pwd']

    cc = ConnectionContext(address=host_c, port=port_c, user=user_c, password=pwd_c, encrypt=True)
    cursor = cc.connection.cursor()
    cursor.execute("""SET SCHEMA GEN_AI""")

    print("[LOG] Successfully connected to Hana Cloud")

    sql = '''SELECT * FROM "CESCO_UNANSWEREDQUESTIONS"'''

    hdf = cc.sql(sql)
    df_result = hdf.collect()
    print(df_result)

#실행
get_unanswerd_questions_data()