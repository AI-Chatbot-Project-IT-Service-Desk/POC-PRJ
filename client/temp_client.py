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

#[20240802 강태영] PDF의 모든 page별 content를 추출하는 함수
def extract_text_from_all_pages(uploaded_file):
    uploaded_file.seek(0)
    doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
    extracted_data = []

    for page_number in range(len(doc)):
        page = doc.load_page(page_number)
        content = extract_content_from_page(page)
        extracted_data.append({
            "page": page_number + 1,
            "content" : content,
        })
    
    return extracted_data

#[20240802 강태영] page의 content를 추출하는 함수(text,font_size,position)
def extract_content_from_page(page):
    blocks = page.get_text("dict")['blocks']
    content = []
    
    for block in blocks:
        if block['type'] == 0:
            for line in block["lines"]:
                for span in line["spans"]:
                    content.append({
                        "type": "text",
                        "text": span["text"].strip(),
                        "font_size": span["size"],
                        "coords": {
                            "x0": block['bbox'][0],
                            "y0": block['bbox'][1],
                            "x1": block['bbox'][2],
                            "y1": block['bbox'][3]
                        }
                    })
    # Sort content by vertical position (y0) and then horizontal position (x0)
    content.sort(key=lambda x: (x["coords"]["y0"], x["coords"]["x0"]))

    return content

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

    return result

#[20240802 강태영] 제목(문제, font 18)을 기준으로 split할 페이지 추출 ex) [{'title': 'PDF 파일 열람 오류', 'page_num': [1, 2]]
def child_page_list(uploaded_file):
    parent_extracted_data = extract_text_from_all_pages(uploaded_file)
    split_child_page_list = []
    temp_bucket = {}
    temp_bucket_num = []

    for page in parent_extracted_data:
        no_large_font_size = True #flag

        for item in page['content']:
            if item['font_size'] >= 18:
                if page['page'] == 1:
                    temp_bucket['title'] = item['text'][:30] #(2024-08-02: 파일명 30자 제한)
                    temp_bucket_num.append(page['page'])
                    no_large_font_size = False
                    break

                temp_bucket['page_num'] = temp_bucket_num
                split_child_page_list.append(temp_bucket)
                
                temp_bucket = {}
                temp_bucket_num = []

                temp_bucket['title'] = item['text'][:30]
                temp_bucket_num.append(page['page'])
                no_large_font_size = False

                break

        if no_large_font_size:
            temp_bucket_num.append(page['page'])

    if len(temp_bucket_num) != 0:
        temp_bucket['page_num'] = temp_bucket_num
        split_child_page_list.append(temp_bucket)
        temp_bucket = {}
        temp_bucket_num = []
        
    return split_child_page_list

#[20240802 강태영] 원본(부모)pdf를 여러 개의 자식 pdf로 분할하여 저장
def split_pdf(uploaded_file, output_pdf_path, page_numbers):
        #원본(부모) PDF 열기
        uploaded_file.seek(0)
        parent_doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")

        #자식 PDF 열기
        child_doc = fitz.open()
        
        #분할할 페이지 지정하기
        for page_num in page_numbers:
            child_doc.insert_pdf(parent_doc, from_page=page_num-1, to_page=page_num-1)
        
        #경로에 새로운 PDF 문서 저장하기
        child_doc.save(output_pdf_path)
        child_doc.close()
        parent_doc.close()
        
#[20240802 강태영] child_page_list함수에서 추출한 페이지 넘버 별로 원본 페이지 몇번
def repeat_split_pdf(uploaded_file, page_output_dir, filename):
    #20240807 강태영 - S3 업로드시 한국어 미지원으로 명명규칙 변경

    cpl = child_page_list(uploaded_file)
    #print(cpl)

    split_file_list = []

    for num in range(len(cpl)):
        #저장 경로 지정하기
        output_pdf_name = f"{filename}_{num}.pdf" 
        output_pdf_path = os.path.join(page_output_dir, output_pdf_name)
        split_file_list.append(output_pdf_name)
        split_pdf(uploaded_file, output_pdf_path, cpl[num]['page_num'])

    return split_file_list

#[20240807] Object Store 업로드
def object_store_upload(uploaded_file, filecode, cesco_division_folder_path):
    s3_configure_path = '../config/s3-service-key-cesco1-interim.txt'

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

    #store = ObjectStore(aws_url, storage_options)
    #store.list()
    aws_pdf_path = os.path.join(aws_url + '/', 'cesco_division_file')
    store = ObjectStore(aws_pdf_path, storage_options)
    print(store.list())

    #원본 파일 업로드
    uploaded_file.seek(0)
    store.put(filecode + '.pdf', uploaded_file.read())

    for division_file in os.listdir(cesco_division_folder_path):
        #print(os.path.join(cesco_division_folder_path + '/', division_file))
        full_path = os.path.join(cesco_division_folder_path + '/', division_file)
        with open(full_path, 'rb') as file:
            pdf_bytes = file.read()
        
        #print(pdf_bytes)

        store.put(division_file, pdf_bytes)
    
    store.list()

#[20240812 강태영] 문제 벡터화 함수
#azure-openai-text-embedding 모델
def get_embedding(input, model = "dc872f9eef04c31a") -> str:
    response = embeddings.create(
        deployment_id = model,
        input = input
    )
    return response.data[0].embedding

#[20240806 강태영] HANA Cloud에 업로드할 Dataframe 만들기
def extract_pdf_to_dataframe(uploaded_file, split_file_list):
    data = extract_text_from_all_pages(uploaded_file)
    df_temp = pd.DataFrame(columns=['text', 'font_size'])

    for page in data:
        for item in page['content']:
            new_row = pd.DataFrame([{'text': item['text'], 'font_size' :item['font_size']}])
            df_temp = pd.concat([df_temp,new_row], ignore_index=True)

    #category 먼저 추출
    category = df_temp[df_temp['font_size'] == 9].iloc[0]['text']
    #print(category)

    #추출했으니 삭제
    df_temp = df_temp[df_temp['font_size'] != 9]

    #클라우드에 넣을 dataframe 생성
    df_final = pd.DataFrame(columns=['ProblemDescription', 'ProblemCategory', 'ProblemKeyword', 'Solution', 'SolutionDoc', 'AdditionalInfo'])

    title = ""
    keyword = ""
    solution = ""
    addtional = ""
    switch_keyword = False
    switch_solution = False
    switch_addtional = False

    for row in df_temp.itertuples(index=True):
        #print(row.Index, row.text, row.font_size)
        if int(row.font_size) == 18 :
            if row.Index == 1:
                title = row.text

                print
            else:               
                #Embedding 진행
                try: 
                    title_vector = get_embedding(title)
                except Exception as e:
                    print(e)

                #print("추가정보의 상태가?", addtional)
                #새로운 질문을 맞이했으니 dataframe에 넣어주기
                new_row = pd.DataFrame([{'ProblemDescription': title, 
                                         'ProblemCategory': category,
                                         'ProblemKeyword': keyword,
                                         'Solution': solution,
                                         'SolutionDoc': '',
                                         'AdditionalInfo': addtional,
                                         'VectorProblem': title_vector}])
                df_final = pd.concat([df_final, new_row], ignore_index=True)

                #새로운 질문 데이터 준비하기
                title = row.text
                keyword = ""
                solution = ""
                addtional = ""
                switch_keyword = False
                switch_solution = False
                switch_addtional = False   

        elif int(row.font_size) == 12:
            if(row.text == "키워드"): 
                switch_keyword = True
                switch_solution = False
                switch_addtional = False
                continue
            elif(row.text == "해결방법"): 
                switch_keyword = False
                switch_solution = True
                switch_addtional = False
                continue
            elif(row.text == "기타내용"):
                switch_keyword = False
                switch_solution = False
                switch_addtional = True
                continue
        
        if switch_keyword :
            keyword += row.text
        if switch_solution :
            solution += row.text
        if switch_addtional :
            addtional += row.text

    if solution != "" :
        #Embedding 진행
        try: 
            title_vector = get_embedding(title)
        except Exception as e:
            print(e)

        new_row = pd.DataFrame([{'ProblemDescription': title, 
                                 'ProblemCategory': category,
                                 'ProblemKeyword': keyword,
                                 'Solution': solution,
                                 'SolutionDoc': '',
                                 'AdditionalInfo': addtional,
                                 'VectorProblem': title_vector}]) #title embedding 해서 넣기
        
        df_final = pd.concat([df_final, new_row], ignore_index=True) 

    #pdf 파일 맵핑
    df_final['SolutionDoc'] = split_file_list

    #print(df_final)

    return df_final

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

    #print(extract_dataframe)

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
        #print(sql)
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

def delete_division_file(page_output_dir):
    if os.path.exists(page_output_dir):
        shutil.rmtree(page_output_dir)
        print(f"[LOG] {page_output_dir} has been deleted.")
    else:
        print(f"[LOG] {page_output_dir} does not exist.")

def main():
    #pdf 파일 업로드
    uploaded_file = st.file_uploader('PDF 파일을 업로드 하세요', type="pdf")
    
    if uploaded_file is not None:
        upload_file_name = (uploaded_file.name).split(".pdf")[0] #업로드한 파일 이름 (확장자 제거)

        #업로드한 파일에서 자식 문제 추출 후 저장할 폴더 경로 지정
        page_output_dir = "../data/cesco_division_file"
        os.makedirs(page_output_dir, exist_ok=True)

        #Object Store S3 한글 미지원 이슈로 인한 파일 이름 코드화 
        filecode = update_FileNamesDB(upload_file_name)
        print("[LOG] filecode ", filecode)

        #자식 PDF 파일 생성
        split_file_list = repeat_split_pdf(uploaded_file, page_output_dir, filecode)
        #print(split_file_list)

        #Object Store S3에 업로드 하기
        object_store_upload(uploaded_file, filecode, page_output_dir)

        #Upload할 DataFrame 생성
        extract_dataframe = extract_pdf_to_dataframe(uploaded_file, split_file_list)

        #HANA CLOUD UPLOAD
        upload_dataframe_to_hanacloud(extract_dataframe)

        #split된 pdf 파일 삭제
        delete_division_file(page_output_dir)
        
if __name__ == "__main__":
    main()