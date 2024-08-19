'''
작성일: 2024-08-19
설명: HANA CLOUD DB CRUD 
'''
import os
import json
import pandas as pd
import hana_ml
from hana_ml import ConnectionContext
from hana_ml.dataframe import create_dataframe_from_pandas

#[20240809 강태영] 업로드한 파일의 코드명을 저장하는 함수
def update_FileNamesDB(upload_file_name):
    result = "" 

    with open(os.path.join(os.getcwd(), '../config/cesco-poc-hc-service-key.json')) as f:
        hana_env_c = json.load(f)
        port_c = hana_env_c['port']
        user_c = hana_env_c['user']
        host_c = hana_env_c['host']
        pwd_c = hana_env_c['pwd']

    cc = ConnectionContext(address=host_c, port=port_c, user=user_c, password=pwd_c, encrypt=True)
    cursor = cc.connection.cursor()
    cursor.execute("""SET SCHEMA GEN_AI""")

    #파일 명이 기존에 이미 저장되어 있는지 없는지 판단
    sql1 = '''SELECT "Code" FROM "CESCO_FILENAMES" WHERE "FileName" = '{upload_file_name}' '''.format(upload_file_name = upload_file_name)
        
    hdf = cc.sql(sql1)
    df_result = hdf.collect()
        
    if df_result.empty:
        #삽입 로직
        sql2 = '''INSERT INTO "CESCO_FILENAMES" ("CodeID", "Code", "FileName")
                VALUES (GEN_AI.FILE_NO.NEXTVAL, 'cesco' || TO_CHAR(GEN_AI.FILE_NO.NEXTVAL), '{upload_file_name}')'''.format(upload_file_name = upload_file_name)
        try:
            cursor.execute(sql2)
        except Exception as e:
            cc.connection.rollback()
            print("An error occurred:", e)
        
        hdf = cc.sql(sql1)
        df_result = hdf.collect()

    result = df_result.loc[0, "Code"]
    
    try:
        cc.connection.commit()
    finally:
        cursor.close()

    cc.connection.setautocommit(True)

    print(f"[SUCCESS] CODE명 {result}")
    return result

#[20240812 강태영] HANA Cloud 에 Dataframe row 단위로 집어넣는 로직
def upload_dataframe_to_hanacloud(extract_dataframe):
    #파일명이 같을 때의 경우 처리 방법 고민 필요(2024-08-12)
    with open(os.path.join(os.getcwd(), '../config/cesco-poc-hc-service-key.json')) as f:
        hana_env_c = json.load(f)
        port_c = hana_env_c['port']
        user_c = hana_env_c['user']
        host_c = hana_env_c['host']
        pwd_c = hana_env_c['pwd']

    cc = ConnectionContext(address=host_c, port=port_c, user=user_c, password=pwd_c, encrypt=True)
    cursor = cc.connection.cursor()
    cursor.execute("""SET SCHEMA GEN_AI""")

    print("[LOG] Successfully connected to Hana Cloud")

    for index, row in extract_dataframe.iterrows():
        sql = '''INSERT INTO "CESCO_PROBLEMSOLUTIONS" (
        "ProblemID", "ProblemDescription", "ProblemCategory", 
        "ProblemKeyword", "Solution", "SolutionDoc", "AdditionalInfo", 
        "VectorProblem", "CreateDate", "UpdateDate")
        VALUES (GEN_AI.PROBLEM_NO.NEXTVAL, '{ProblemDescription}', '{ProblemCategory}',
        '{ProblemKeyword}', '{Solution}', '{SolutionDoc}', '{AdditionalInfo}',
        TO_REAL_VECTOR('{VectorProblem}'), CURRENT_DATE, CURRENT_DATE)'''.format(ProblemDescription = row['ProblemDescription'],
                                                               ProblemCategory = row['ProblemCategory'],
                                                               ProblemKeyword = row['ProblemKeyword'],
                                                               Solution = row['Solution'],
                                                               SolutionDoc = row['SolutionDoc'],
                                                               AdditionalInfo = row['AdditionalInfo'],
                                                               VectorProblem = row['VectorProblem'])
        
        try:
            cursor.execute(sql)
        except Exception as e:
            cc.connection.rollback()
            print("An error occurred:", e)
        
        try:
            cc.connection.commit()
        finally:
            cursor.close()
        cc.connection.setautocommit(True)

    print("[LOG] Successfully uploaded to HANA Cloud.")