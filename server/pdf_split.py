'''
작성일: 2024-08-19
설명: PDF Split Logic
'''
import fitz  # PyMuPDF
import os
from pathlib import Path
import pandas as pd
from gen_ai_hub.proxy.native.openai import embeddings
import shutil
from server import gen_ai_model_service as gams
# from transformers import AutoTokenizer, AutoModel
# import torch
# import tokenizers

#[20240802 강태영] PDF의 모든 page별 content를 추출하는 함수
def extract_text_from_all_pages(type , uploaded_file):
    if type == "parent":
        uploaded_file.seek(0)
        doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
    elif type == "child":
        doc = fitz.open(uploaded_file)

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

#[20240819 강태영] 지정된 양식 파일에 맞춰 업로드 하였는지 여부 확인
def check_form(uploaded_file):
    doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
    page = doc.load_page(0)
    content = extract_content_from_page(page)
    for data in reversed(content):
        if data['text'] == "224632306323587" or int(data['font_size']) == 9 :
            return True
    
    return False

#[20240827 강태영] FileNames 테이블에 카테고리 저장 추가
def extract_file_category(uploaded_file):
    uploaded_file.seek(0)
    doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
    page = doc.load_page(0)
    content = extract_content_from_page(page)

    result = content[0]['text']

    return result

#[20240802 강태영] 제목(문제, font 18)을 기준으로 split할 페이지 추출 ex) [{'title': 'PDF 파일 열람 오류', 'page_num': [1, 2]]
def child_page_list(uploaded_file):
    parent_extracted_data = extract_text_from_all_pages("parent", uploaded_file)
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

#[20240802 강태영] child_page_list함수에서 추출한 페이지 넘버 별로 split 반복
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

#[20240812 강태영] 문제 벡터화 함수
#azure-openai-text-embedding 모델
# def get_embedding_gen_ai(input, model = "dc872f9eef04c31a") -> str:
#     response = embeddings.create(
#         deployment_id = model,
#         input = input
#     )
#     return response.data[0].embedding

#[20240819 강태영] 자식 PDF → PROBLEMSOLUTIONS DB의 ROW로 생성 → HANA CLOUD UPDATE
def extreact_pdf_to_dataframe(page_output_dir):

    pdf_files = Path(page_output_dir).glob('*.pdf')

    df_final = pd.DataFrame(columns=['ProblemDescription', 'ProblemCategory', 'ProblemKeyword', 'Solution', 'SolutionDoc', 'AdditionalInfo'])

    for pdf_file in pdf_files:
        temp_data = {'text': [], 'font_size': []}

        data = extract_text_from_all_pages("child", pdf_file)

        for page in data:
            for item in page['content']:
                temp_data['text'].append(item['text'])
                temp_data['font_size'].append(item['font_size'])

                #new_row = pd.DataFrame([{'text': item['text'], 'font_size' :item['font_size']}])
                #df_temp = pd.concat([df_temp,new_row], ignore_index=True)

        df_temp = pd.DataFrame(temp_data, columns=['text', 'font_size'])

        #category 추출
        category = df_temp[df_temp['font_size'] == 9].iloc[0]['text']

        #추출 후 fontsize 9 삭제
        df_temp = df_temp[df_temp['font_size'] != 9]

        title = ""
        keyword = ""
        solution = ""
        addtional = ""
        switch_keyword = False
        switch_solution = False
        switch_addtional = False

        for row in df_temp.itertuples(index=True):
            if int(row.font_size) == 18:
                title += row.text
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

        try: 
            #[20240830 강태영] 제목만 벡터화 하지 않고 제목과 키워드도 같이 벡터화한다
            vector_text = f"keyword: {keyword}, content: {title}"
            title_vector = gams.get_embedding(vector_text)
        except Exception as e:
            print(e)

        new_row = pd.DataFrame([{'ProblemDescription': title, 
                                 'ProblemCategory': category,
                                 'ProblemKeyword': keyword,
                                 'Solution': solution,
                                 'SolutionDoc': pdf_file.name,
                                 'AdditionalInfo': addtional,
                                 'VectorProblem': title_vector}]) #title embedding 해서 넣기
        
        df_final = pd.concat([df_final, new_row], ignore_index=True)

    print("[LOG] DataFrame successfully created.")
    return df_final


def delete_division_file(page_output_dir):
    if os.path.exists(page_output_dir):
        shutil.rmtree(page_output_dir)
        print(f"[LOG] {page_output_dir} has been deleted.")
    else:
        print(f"[LOG] {page_output_dir} does not exist.")
