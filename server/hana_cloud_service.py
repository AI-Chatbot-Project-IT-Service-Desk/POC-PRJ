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
from gen_ai_hub.proxy.native.openai import embeddings
from langchain_core.prompts import PromptTemplate
from gen_ai_hub.proxy.langchain.openai import ChatOpenAI
from gen_ai_hub.proxy.core.proxy_clients import get_proxy_client
proxy_client = get_proxy_client('gen-ai-hub')

with open(os.path.join(os.getcwd(), './config/cesco-poc-hc-service-key.json')) as f:
    hana_env_c = json.load(f)
    port_c = hana_env_c['port']
    user_c = hana_env_c['user']
    host_c = hana_env_c['host']
    pwd_c = hana_env_c['pwd']

cc = ConnectionContext(address=host_c, port=port_c, user=user_c, password=pwd_c, encrypt=True)
cursor = cc.connection.cursor()
cursor.execute("""SET SCHEMA GEN_AI""")

def is_aready_exist_pdf_file(upload_file_name):
    # with open(os.path.join(os.getcwd(), './config/cesco-poc-hc-service-key.json')) as f:
    #     hana_env_c = json.load(f)
    #     port_c = hana_env_c['port']
    #     user_c = hana_env_c['user']
    #     host_c = hana_env_c['host']
    #     pwd_c = hana_env_c['pwd']

    # cc = ConnectionContext(address=host_c, port=port_c, user=user_c, password=pwd_c, encrypt=True)
    # cursor = cc.connection.cursor()
    # cursor.execute("""SET SCHEMA GEN_AI""")

    sql = '''SELECT COUNT(*)
             FROM (	SELECT "ProblemCategory"
                    FROM gen_ai.cesco_problemsolutions
                    GROUP BY "ProblemCategory")
             WHERE "ProblemCategory" = '{upload_file_name}' '''.format(upload_file_name = upload_file_name)

    hdf = cc.sql(sql)
    df_result = hdf.collect()

    name_count_value = df_result.iloc[0]["COUNT(*)"]

    if int(name_count_value) == 0 :
        #기존에 저장되어 있는 PDF 파일 명이 없습니다
        return False
    
    return True

#[20240809 강태영] 업로드한 파일의 코드명을 저장하는 함수
def update_FileNamesDB(file_category):
    result = "" 

    # with open(os.path.join(os.getcwd(), './config/cesco-poc-hc-service-key.json')) as f:
    #     hana_env_c = json.load(f)
    #     port_c = hana_env_c['port']
    #     user_c = hana_env_c['user']
    #     host_c = hana_env_c['host']
    #     pwd_c = hana_env_c['pwd']

    # cc = ConnectionContext(address=host_c, port=port_c, user=user_c, password=pwd_c, encrypt=True)
    # cursor = cc.connection.cursor()
    # cursor.execute("""SET SCHEMA GEN_AI""")

    #파일 명이 기존에 이미 저장되어 있는지 없는지 판단
    sql1 = '''SELECT "Code" 
              FROM "CESCO_FILENAMES" 
              WHERE "FileName" = '{file_category}' '''.format(file_category = file_category)
        
    hdf = cc.sql(sql1)
    df_result = hdf.collect()
        
    if df_result.empty:
        #삽입 로직
        sql2 = '''INSERT INTO "CESCO_FILENAMES" ("CodeID", "Code", "FileName", "CreateDate")
                VALUES (GEN_AI.FILE_NO.NEXTVAL, 'cesco' || TO_CHAR(GEN_AI.FILE_NO.NEXTVAL), '{file_category}', CURRENT_DATE)'''.format(file_category = file_category)
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
def upload_dataframe_to_hanacloud(extract_dataframe, filecode):
    #파일명이 같을 때의 경우 처리 방법 고민 필요(2024-08-12)
    # with open(os.path.join(os.getcwd(), './config/cesco-poc-hc-service-key.json')) as f:
    #     hana_env_c = json.load(f)
    #     port_c = hana_env_c['port']
    #     user_c = hana_env_c['user']
    #     host_c = hana_env_c['host']
    #     pwd_c = hana_env_c['pwd']

    # cc = ConnectionContext(address=host_c, port=port_c, user=user_c, password=pwd_c, encrypt=True)
    # cursor = cc.connection.cursor()
    # cursor.execute("""SET SCHEMA GEN_AI""")

    print("[LOG] Successfully connected to Hana Cloud")

    for index, row in extract_dataframe.iterrows():
        sql = '''INSERT INTO "CESCO_PROBLEMSOLUTIONS" (
        "ProblemID", "ProblemDescription", "ProblemCategory", 
        "ProblemKeyword", "Solution", "SolutionDoc", "AdditionalInfo", "Code",
        "VectorProblem", "CreateDate", "UpdateDate")
        VALUES (GEN_AI.PROBLEM_NO.NEXTVAL, '{ProblemDescription}', '{ProblemCategory}',
        '{ProblemKeyword}', '{Solution}', '{SolutionDoc}', '{AdditionalInfo}', '{filecode}',
        TO_REAL_VECTOR('{VectorProblem}'), CURRENT_DATE, CURRENT_DATE)'''.format(ProblemDescription = row['ProblemDescription'].replace("'","''"),
                                                               ProblemCategory = row['ProblemCategory'].replace("'","''"),
                                                               ProblemKeyword = row['ProblemKeyword'].replace("'","''"),
                                                               Solution = row['Solution'].replace("'","''"),
                                                               SolutionDoc = row['SolutionDoc'],
                                                               AdditionalInfo = row['AdditionalInfo'].replace("'","''"),
                                                               filecode = filecode,
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

#[20240828 강태영] CESCO_FILENAMES(원본 테이블) 조회
def select_all_filenames_table():
    # with open(os.path.join(os.getcwd(), './config/cesco-poc-hc-service-key.json')) as f:
    #     hana_env_c = json.load(f)
    #     port_c = hana_env_c['port']
    #     user_c = hana_env_c['user']
    #     host_c = hana_env_c['host']
    #     pwd_c = hana_env_c['pwd']

    # cc = ConnectionContext(address=host_c, port=port_c, user=user_c, password=pwd_c, encrypt=True)
    # cursor = cc.connection.cursor()
    # cursor.execute("""SET SCHEMA GEN_AI""")

    sql1 = '''SELECT "FileName", "CreateDate", CONCAT("Code", '.pdf') FROM gen_ai.cesco_filenames;'''
        
    hdf = cc.sql(sql1)
    df_result = hdf.collect()    

    return df_result

#[20240830 강태영] QNA 테이블 조회
def select_all_problemsolutions_table():
    # with open(os.path.join(os.getcwd(), './config/cesco-poc-hc-service-key.json')) as f:
    #     hana_env_c = json.load(f)
    #     port_c = hana_env_c['port']
    #     user_c = hana_env_c['user']
    #     host_c = hana_env_c['host']
    #     pwd_c = hana_env_c['pwd']

    # cc = ConnectionContext(address=host_c, port=port_c, user=user_c, password=pwd_c, encrypt=True)
    # cursor = cc.connection.cursor()
    # cursor.execute("""SET SCHEMA GEN_AI""")

    sql1 = '''SELECT "ProblemCategory", "ProblemDescription", "CreateDate", "SolutionDoc" FROM gen_ai.cesco_problemsolutions;'''
        
    hdf = cc.sql(sql1)
    df_result = hdf.collect()    

    return df_result

#[20240902 강태영] 임베딩
def get_embedding(input, model="dc872f9eef04c31a") -> str:
    response = embeddings.create(
        deployment_id = model,
        input = input
    )
    return response.data[0].embedding

#[20240902 강태영] 벡터서치
def run_vector_search(query: str, metric="COSINE_SIMILARITY", k=5):
    # with open(os.path.join(os.getcwd(), '../config/cesco-poc-hc-service-key.json')) as f:
    #     hana_env_c = json.load(f)
    #     port_c = hana_env_c['port']
    #     user_c = hana_env_c['user']
    #     host_c = hana_env_c['host']
    #     pwd_c = hana_env_c['pwd']

    # cc = ConnectionContext(address=host_c, port=port_c, user=user_c, password=pwd_c, encrypt=True)
    # cursor = cc.connection.cursor()
    # cursor.execute("""SET SCHEMA GEN_AI""")

    if metric == 'L2DISTANCE':
        sort = 'ASC'
        col = 'L2D_SIM'
    elif metric == 'COSINE_SIMILARITY':
        sort = 'DESC'
        col = 'COS_SIM'

    query_vector = get_embedding(query)

    sql = '''SELECT TOP {k} "ProblemDescription","ProblemCategory", "ProblemKeyword",
    "Solution","SolutionDoc", "AdditionalInfo",
    "Code", "{metric}"("VectorProblem", TO_REAL_VECTOR('{qv}'))
    AS "{col}", "CreateDate", "UpdateDate"
    FROM "CESCO_PROBLEMSOLUTIONS"
    ORDER BY "{col}" {sort}
    '''.format(k=k, metric = metric, qv = query_vector, sort=sort, col=col)

    hdf = cc.sql(sql)
    df_context = hdf.collect()

    return df_context

#[20240902 강태영] LangChain
promptTemplate_fstring = """
You are a friendly and helpful AI assistant.
Based on the provided context, please answer the user's question in a clear and polite manner, ensuring the response is easy to understand. 
Make sure to include all the content from the provided context and do not omit any details. 
If there is information under "etc", include that additional information in your answer as well.
Context:
{context}
Question:
{query}
Answer:
"""

promptTemplate = PromptTemplate.from_template(promptTemplate_fstring)

def ask_llm(query: str, k1_context: pd.Series) -> str:
    context = f"""category: {k1_context["ProblemCategory"]}, keyword: {k1_context["ProblemKeyword"]}, content: {k1_context["ProblemDescription"]}, {k1_context["Solution"]}, etc: {k1_context["AdditionalInfo"]}"""
    prompt = promptTemplate.format(query=query, context=context)
    print('\nAsking LLM...')
    llm = ChatOpenAI(deployment_id="d03974e89ef130ad", temperature=0)
    response = llm.invoke(prompt)
    return response.content

#[20240904 강태영]
def upload_unanswered_data(prompt: str):

    #미응답 테이블에 똑같은 질문이 들어 있다면 INSERT 하지 않는다
    sql = '''SELECT count(*) FROM gen_ai.cesco_unansweredquestions
            WHERE "QuestionText" = '{text}' '''.format(text=prompt)
    
    hdf = cc.sql(sql)
    df_result = hdf.collect()

    is_exist = df_result.iloc[0]["COUNT(*)"]

    if int(is_exist) == 0: 
        sql_command = '''INSERT INTO "CESCO_UNANSWEREDQUESTIONS" (
        "QuestionID", "QuestionText", "Status", "StatusUpdateDate", "DownloadDate", "CreateDate")
        VALUES (GEN_AI.UNANSWER_NO.NEXTVAL, '{text}', '미처리', CURRENT_DATE, CURRENT_DATE, CURRENT_DATE)'''.format(text=prompt)

        try:
            cursor.execute(sql_command)
        except Exception as e:
            cc.connection.rollback()
            print("An error occurred:", e)

        try:
            cc.connection.commit()
        finally:
            cursor.close()

        cc.connection.setautocommit(True)