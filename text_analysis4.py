# # 필요한 라이브러리 설치
# !pip install konlpy
# !pip install scikit-learn
# !pip install pandas
# !pip install matplotlib

# 라이브러리 불러오기
import os
import io
import time
import streamlit as st
import json
import pandas as pd
import pecab
import hana_ml
from streamlit_pagination import pagination_component
from hana_ml import ConnectionContext
from hana_ml.dataframe import create_dataframe_from_pandas
from gen_ai_hub.proxy.native.openai import embeddings
from konlpy.tag import Okt
from sklearn.feature_extraction.text import TfidfVectorizer
from collections import Counter
import matplotlib.pyplot as plt
import koreanize_matplotlib

# 텍스트 데이터 리스트 (약 20개의 텍스트 데이터가 있다고 가정)
# texts = [
#     "SC 법인 차량에 에어컨이 안나옵니다.",
#     "차세대시스템 내 DB 구조가 궁금합니다.",
#     "DATA를 DB에 올리는 방법이 궁금합니다.",
#     "바퀴벌레 해충 동정 법이 궁금합니다.",
#     "시궁쥐와 들쥐의 차이점이 궁금합니다.",
#     "세스코 터치센터의 주소가 궁금해요.",
#     "세스카페의 아메리카노 가격이 궁금합니다.",
#     "세스코 터치센터 근처 버스정류장이 어디있나요",
#     "터치센터에서 강일역 가능 방법이 궁금해요",
#     "셔틀버스 탑승 시간을 알려주세요.",
#     "출근 할 때 잠실역에서 셔틀버스 어디서 타는지 알고 싶어요.",
#     "본사 직원 출근 시간이 궁금합니다.",
#     "IT 서비스 데스크 직통 번호를 알려주세요.",
#     "회사에서 지급한 노트북이 고장났어요.",
#     "윈도우 설치 방법이 궁금합니다.",
#     "세스톡 로그인이 안됩니다.",
#     "연차 신청 방법이 궁금합니다.",
#     "내 연차가 얼마나 남았는지 궁금해.",
#     "이번 달 월급 명세서 확인하려면 어디로 가야하나요",
#     "회사창립기념일이 언제인가요?"

# ]
with open(os.path.join(os.getcwd(), r"C:\Users\cesco\Desktop\code file\AI PoC\POC-PRJ\config\cesco-poc-hc-service-key.json")) as f:
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
print(hdf)
df = hdf.collect()
texts = df['QuestionText'].tolist()

column_mapping = {
    'QuestionID': '미응답 ID',
    'QuestionText': '미응답 내용',
    'Status': '처리 상태',
    'StatusUpdateDate': '질문 처리일',
    'DownloadDate': '다운로드 진행일',
    'CreateDate': '질문 생성일',
    # 추가적인 컬럼 이름 변경
}

# 페이지당 항목 수
n = 10

# 데이터 청크 생성
list_df = [df[i:i+n] for i in range(0, df.shape[0], n)]

# 페이지네이션 컴포넌트 생성 및 상태 업데이트
def data_chunk_choice():
    if 'foo' not in st.session_state:
        st.session_state['foo'] = 0  # 초기값 설정
    return st.session_state.get('foo', 0)

# 페이지네이션 레이아웃 설정
layout = {
    'color': "primary",
    'style': {'margin-top': '10px'}
}

# 페이지네이션 컴포넌트 호출
current_page = pagination_component(len(list_df), layout=layout, key="foo")

if current_page is None:
    current_page = 0
    st.session_state['foo'] = current_page  # None일 때 0으로 설정

# 현재 페이지에 해당하는 데이터 청크 선택
data_l = list_df[data_chunk_choice()]

# 데이터프레임 출력
st.title("미응답 테이블")
st.dataframe(data_l)

# 디버깅을 위한 출력
st.write(f"Current page: {data_chunk_choice()}")
st.write(f"Total pages: {len(list_df)}")

# def data_chunk_choice():
#     if 'foo' not in st.session_state:
#         return 0
#     return st.session_state['foo']

# n = 10
# list_df = [df[i:i+n] for i in range(0,df.shape[0],n)]
# print(list_df)
# data_l = list_df[data_chunk_choice()]
# # data_l = list_df[data_chunk_choice()]
# # css 적용
st.markdown('<style>' + open(r'streamlit_pagination\style.css').read() + '</style>', unsafe_allow_html=True)
# st.title("미응답 테이블")
# st.dataframe(data_l)
# layout = {  'color':"primary", 
#             'style':{'margin-top':'10px'}}
# test = pagination_component(len(list_df), layout=layout, key="foo")
# 페이지당 항목 수
# items_per_page = 10

# # 총 페이지 수 계산
# total_pages = (len(df) + items_per_page - 1) // items_per_page

# # 페이지네이션 컴포넌트 생성
# # current_page = pagination_component(total_pages, layout={"color": "primary"})
# layout = {  'color':"primary", 
#             'style':{'margin-top':'10px'}}
# current_page = pagination_component(total_pages, layout=layout, key="foo")
# current_page_2 = current_page + 1 if current_page is not None else 1

# # 페이지네이션에 따라 데이터 슬라이싱
# start_idx = (current_page_2 - 1) * items_per_page
# end_idx = min(current_page_2 * items_per_page, len(df))

# data_l = df.iloc[start_idx:end_idx].reset_index(drop=True)

# # 데이터프레임 출력
# st.dataframe(df.iloc[start_idx:end_idx].reset_index(drop=True), hide_index=True)


# # 페이지 네비게이션에 대한 정보 표시 (디버깅용)
# st.write(f"Showing page {current_page_2} of {total_pages}")

# total_pages = len(df) // 10 + 1
# current_page = pagination_component(total_pages, layout={"color": "primary"})
# print(current_page)
# # page = st.slider('페이지 넘버', 1, total_pages, 1)
# start_idx = (current_page + 1) * 10
# end_idx = min(current_page * 10, len(df))
# print(start_idx)
# print(end_idx)

# # 10개 단위로 테이블을 보여주기 (인덱스 없이)
# st.dataframe(df.iloc[start_idx:end_idx].reset_index(drop=True), hide_index=True)

# xlsx 다운로드 버튼 추가
def to_excel(df):
    """ Convert DataFrame to Excel file and return as bytes. """
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Sheet1')
    return output.getvalue()

# Convert DataFrame to Excel file
excel_data = to_excel(df)

# Download button for Excel file
st.download_button(
    label="엑셀 파일 다운로드",
    data=excel_data,
    file_name='unanswered_table.xlsx',
    mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
)

# 형태소 분석기 초기화
pecab = pecab.PeCab()

# 텍스트를 형태소로 분석하여 명사만 추출
# tokenized_texts = [' '.join(okt.nouns(text)) for text in texts]
tokenized_texts = [' '.join([word for word, pos in pecab.pos(text) if pos == 'NNG' or pos == 'NNP']) for text in texts]


# TF-IDF를 사용하여 불용어 제거
tfidf = TfidfVectorizer(min_df=1, max_df=0.5)  # max_df=0.5는 TF-IDF 점수가 높은 단어들만 포함
tfidf_matrix = tfidf.fit_transform(tokenized_texts)
feature_names = tfidf.get_feature_names_out()

# TF-IDF 값이 0 이상인 단어들만 추출
filtered_words = []
for doc_idx in range(tfidf_matrix.shape[0]):
    for word_idx, score in zip(tfidf_matrix[doc_idx].indices, tfidf_matrix[doc_idx].data):
        if score > 0:
            filtered_words.append(feature_names[word_idx])

# 필터링된 단어의 빈도수 계산
word_count = Counter(filtered_words)

# 빈도수 상위 10개 단어 출력
most_common_words = word_count.most_common(10)

# Pandas Series로 변환
word_series = pd.Series(dict(most_common_words))

# 그래프로 출력
# plt.figure(figsize=(10, 6))
# word_series.plot(kind='bar')
# plt.title('Top 10 Most Frequent Words')
# plt.xlabel('Words')
# plt.ylabel('Frequency')
# plt.xticks(rotation=45)
# plt.show()

# page = st.number_input('페이지 넘버', min_value=1, max_value=len(df)//10 + 1, value=1)
# st.dataframe(df.iloc[(page-1)*10:page*10].reset_index(drop=True), hide_index=True)

st.subheader("형태소 분석 결과 - Top 10 미응답 단어")

fig, ax = plt.subplots(figsize=(10, 6))
word_series.plot(kind='bar', color='skyblue', ax=ax)
ax.set_title('Top 10 Words by TF-IDF Score')
ax.set_xlabel('Words')
ax.set_ylabel('TF-IDF Score')

st.pyplot(fig)
