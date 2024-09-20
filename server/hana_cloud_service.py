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

from server import gen_ai_model_service as gams

proxy_client = get_proxy_client('gen-ai-hub')

#연결
with open(os.path.join(os.getcwd(), './config/cesco-poc-hc-service-key.json')) as f:
    hana_env_c = json.load(f)
    port_c = hana_env_c['port']
    user_c = hana_env_c['user']
    host_c = hana_env_c['host']
    pwd_c = hana_env_c['pwd']

cc = ConnectionContext(address=host_c, port=port_c, user=user_c, password=pwd_c, encrypt=True)
cursor = cc.connection.cursor()
cursor.execute("""SET SCHEMA GEN_AI""")

print("[START] HANA CLOUD DB Connect Success")

def is_aready_exist_pdf_file(upload_file_name):
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
    sql1 = '''SELECT "CodeID", "FileName", "CreateDate", CONCAT("Code", '.pdf') FROM gen_ai.cesco_filenames'''

    hdf = cc.sql(sql1)
    df_result = hdf.collect()    

    return df_result

def select_all_unansweredquestions_table():
    sql = '''SELECT "CreateDate", "StatusUpdateDate", "QuestionText", "Status" FROM "CESCO_UNANSWEREDQUESTIONS"'''

    hdf = cc.sql(sql)
    df = hdf.collect()

    return df

#[20240830 강태영] QNA 테이블 조회
def select_all_problemsolutions_table():
    sql1 = '''SELECT "ProblemCategory", "ProblemDescription", "CreateDate", "SolutionDoc" FROM gen_ai.cesco_problemsolutions;'''
        
    hdf = cc.sql(sql1)
    df_result = hdf.collect()    

    return df_result

#[20240902 강태영] 임베딩
# def get_embedding(input, model="dc872f9eef04c31a") -> str:
#     response = embeddings.create(
#         deployment_id = model,
#         input = input
#     )
#     return response.data[0].embedding

#[20240902 강태영] 벡터서치
def run_vector_search(query: str, metric="COSINE_SIMILARITY", k=5):
    if metric == 'L2DISTANCE':
        sort = 'ASC'
        col = 'L2D_SIM'
    elif metric == 'COSINE_SIMILARITY':
        sort = 'DESC'
        col = 'COS_SIM'

    query_vector = gams.get_embedding(query)

    sql = '''SELECT TOP {k} "ProblemDescription","ProblemCategory", "ProblemKeyword",
    "Solution","SolutionDoc", "AdditionalInfo",
    "Code", "{metric}"("VectorProblem", TO_REAL_VECTOR('{qv}'))
    AS "{col}", "CreateDate", "UpdateDate"
    FROM "CESCO_PROBLEMSOLUTIONS"
    ORDER BY "{col}" {sort}
    '''.format(k=k, metric = metric, qv = query_vector, sort=sort, col=col)

    hdf = cc.sql(sql)
    df_context = hdf.collect()

    print("[LOG] GET K5 IS SUCCESS")
    
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
    #llm = ChatOpenAI(deployment_id="d36b7697328746e0", temperature=0)

    response = llm.invoke(prompt)
    print("[LOG] 답변 생성 완료")
    return response.content

#[20240904 강태영] 무응답 답변 등록 
def upload_unanswered_data(unquestion: str):

    #미응답 테이블에 똑같은 질문이 들어 있다면 INSERT 하지 않는다
    sql = '''SELECT count(*) FROM gen_ai.cesco_unansweredquestions
            WHERE "QuestionText" = '{text}' '''.format(text=unquestion)
    
    hdf = cc.sql(sql)
    df_result = hdf.collect()

    is_exist = df_result.iloc[0]["COUNT(*)"]

    if int(is_exist) == 0: 
        sql_command = '''INSERT INTO "CESCO_UNANSWEREDQUESTIONS" (
        "QuestionID", "QuestionText", "Status", "StatusUpdateDate", "DownloadDate", "CreateDate")
        VALUES (GEN_AI.UNANSWER_NO.NEXTVAL, '{text}', '미처리', CURRENT_DATE, CURRENT_DATE, CURRENT_DATE)'''.format(text=unquestion)

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

        return True
    else:
        return False

#[20240905 강태영] 매뉴얼 데이터 전체 조회
def get_menual_data():

    sql = '''SELECT "ProblemCategory", "ProblemKeyword", "ProblemDescription", "SolutionDoc", "CreateDate"
             FROM gen_ai.cesco_problemsolutions '''
    
    hdf = cc.sql(sql)
    df_result = hdf.collect()

    return df_result

#[20240911 강태영] 삭제할 코드 명 SELECT
def select_code_list(deleted_rows):

    delete_list = ", ".join(map(str, deleted_rows))

    sql = '''select "Code" from gen_ai.cesco_filenames
                where "CodeID" in ({delete_list})'''.format(delete_list = delete_list)
    
    hdf = cc.sql(sql)
    df_result = hdf.collect()

    code_list = df_result["Code"]

    return code_list.tolist()

#[20240911 강태영] 원본 파일 삭제 
def remove_selected_files(deleted_rows):

    delete_list = ", ".join(map(str, deleted_rows))

    sql = '''delete from gen_ai.cesco_filenames
                where "CodeID" in ({delete_list})'''.format(delete_list = delete_list)

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

    print("[LOG] Successfully deleted to HANA Cloud.")

#[20240911 강태영] 자식 파일 삭제 대상 select
def select_child_pdf_list(code_list): 
    code_map_list = ", ".join(f"'{item}'" for item in code_list)

    sql = '''select "SolutionDoc" from gen_ai.cesco_problemsolutions
            where "Code" in ({code_map_list})'''.format(code_map_list = code_map_list)
    hdf = cc.sql(sql)

    df_result = hdf.collect()

    result = df_result["SolutionDoc"]

    return result.tolist()

#[20240911 강태영] 자식 파일 삭제 대상 삭제 
def remove_child_files(code_list):
    code_map_list = ", ".join(f"'{item}'" for item in code_list)

    sql = '''delete from gen_ai.cesco_problemsolutions
            where "Code" in ({code_map_list});'''.format(code_map_list = code_map_list)
    
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

    print("[LOG] Successfully deleted to HANA Cloud.")

#[20240912 강진욱] 무응답 테이블 조회
def select_all_unansweredquestions_table():
    sql = '''SELECT "QuestionID", "CreateDate", "StatusUpdateDate", "QuestionText", "Status" FROM "CESCO_UNANSWEREDQUESTIONS"'''

    hdf = cc.sql(sql)
    df = hdf.collect()

    return df

#[20240912 강태영]무응답 테이블 row 삭제
def remove_selected_unanswered(drop_indexes):
    index_map_list =  ", ".join(map(str, drop_indexes))

    sql = '''delete from gen_ai.cesco_unansweredquestions
            where "QuestionID" in ({index_map_list})'''.format(index_map_list = index_map_list)
    
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

    print("[LOG] Successfully deleted to HANA Cloud.")

#[20240919 강태영]무응답 테이블 상태 수정
def updated_unanswered_status(update_state_index, update_state_value):
    
    sql = '''UPDATE gen_ai.cesco_unansweredquestions 
            SET "Status" = '{update_state_value}', "StatusUpdateDate" = CURRENT_DATE
            WHERE "QuestionID" = {update_state_index} '''.format(update_state_value = update_state_value,
                                                                 update_state_index = update_state_index)
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

    print("[LOG] Successfully updated to HANA Cloud.")