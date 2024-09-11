import os
import io
import streamlit as st
import json
import pandas as pd
import pecab
import hana_ml
from hana_ml import ConnectionContext
from hana_ml.dataframe import create_dataframe_from_pandas
from gen_ai_hub.proxy.native.openai import embeddings
from sklearn.feature_extraction.text import TfidfVectorizer
from collections import Counter
import matplotlib.pyplot as plt
import koreanize_matplotlib
from menu import menu_with_redirect

# Redirect to app.py if not logged in, otherwise show the navigation menu
menu_with_redirect()

with open(os.path.join(os.getcwd(), r"./config/cesco-poc-hc-service-key.json")) as f:
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
df = hdf.collect()
texts = df['QuestionText'].tolist()

# 형태소 분석기 초기화
pecab = pecab.PeCab()

# 텍스트를 형태소로 분석하여 명사만 추출
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

top_word = word_series.idxmax()
top_word_count = word_series.max()
missing_data_count = df.shape[0]
completed_status_count = df[df['Status'] == '처리 완료'].shape[0]
total_count = df.shape[0]
completed_percentage = (completed_status_count / total_count) * 100

st.title("무응답 데이터 관리 페이지")

col1, col2, col3 = st.columns(3)

# col1: 가장 많은 빈도수를 차지한 단어 표현
col1.metric("Most Common Word", f"{top_word}", f"{top_word_count} occurrences")

# col2: 총 미응답 데이터 수
col2.metric("Missing Data Count", str(missing_data_count))

# col3: '처리 완료' 비율
col3.metric("Completion Rate", f"{completed_percentage:.2f}%", "Percentage of completed status")

st.subheader("형태소 분석 결과 - Top 10 미응답 단어")

fig, ax = plt.subplots(figsize=(10, 6))
word_series.plot(kind='bar', color='skyblue', ax=ax)
ax.set_title('Top 10 Words by TF-IDF Score')
ax.set_xlabel('Words')
ax.tick_params(axis='x', rotation=0)
ax.set_ylabel('TF-IDF Score')

st.pyplot(fig)

# df2 = st.data_editor(df.reset_index(drop=True), hide_index=True)
def paginate_data(df, items_per_page):
    # 총 페이지 수 계산
    total_pages = len(df) // items_per_page + (1 if len(df) % items_per_page > 0 else 0)

    # 현재 페이지 선택
    page = st.number_input("페이지 번호", min_value=1, max_value=total_pages, value=1)
    
    # 해당 페이지 데이터 추출
    start_idx = (page - 1) * items_per_page
    end_idx = start_idx + items_per_page
    current_data = df.iloc[start_idx:end_idx]
    
    # 페이지네이션 정보 반환
    return current_data, page, total_pages

# 데이터 페이지네이션 적용 (10개씩 구분)
items_per_page = 10
current_data, page, total_pages = paginate_data(df, items_per_page)

# 현재 페이지의 데이터 출력
st.data_editor(current_data.reset_index(drop=True),
                        hide_index=True,
                        column_config={ 'Select': st.column_config.CheckboxColumn("Your favorite?", default=False),
                                        'QuestionID': st.column_config.Column(disabled=True),
                                        'QuestionText': st.column_config.Column(disabled=True),
                                        'Status': st.column_config.SelectboxColumn(disabled=False,
                                                                                    width="small",
                                                                                    options=[
                                                                                        "미처리",
                                                                                        "처리 완료",
                                                                                        "보류"
                                                                                    ],
                                                                                    default="미처리",
                                                                                    required=True),
                                        'StatusUpdateDate': st.column_config.Column(disabled=True),
                                        'DownloadDate': st.column_config.Column(disabled=True),
                                        'CreateDate': st.column_config.Column(disabled=True)
                                    },
                        # num_rows="dynamic"  # 행 추가 기능 비활성화
                        )

# 페이지네이션 정보 표시
st.write(f"Page {page} of {total_pages}")



# sql = '''SELECT * FROM "CESCO_UNANSWEREDQUESTIONS"'''
# hdf = cc.sql(sql)
# df = hdf.collect()
# texts = df['QuestionText'].tolist()


# # 형태소 분석 및 TF-IDF 처리 함수
# def process_texts(df, pecab):
#     texts = df['QuestionText'].tolist()
#     tokenized_texts = [' '.join([word for word, pos in pecab.pos(text) if pos in ['NNG', 'NNP']]) for text in texts]
    
#     tfidf = TfidfVectorizer(min_df=1, max_df=0.5)
#     tfidf_matrix = tfidf.fit_transform(tokenized_texts)
#     feature_names = tfidf.get_feature_names_out()

#     filtered_words = [feature_names[word_idx] for doc_idx in range(tfidf_matrix.shape[0]) 
#                       for word_idx, score in zip(tfidf_matrix[doc_idx].indices, tfidf_matrix[doc_idx].data) if score > 0]
    
#     word_count = Counter(filtered_words)
#     return pd.Series(dict(word_count.most_common(10)))

# # 페이지네이션 함수
# def paginate_data(df, items_per_page):
#     total_pages = len(df) // items_per_page + (1 if len(df) % items_per_page > 0 else 0)
#     page = st.number_input("페이지 번호", min_value=1, max_value=total_pages, value=1)
    
#     start_idx = (page - 1) * items_per_page
#     end_idx = start_idx + items_per_page
#     return df.iloc[start_idx:end_idx], page, total_pages

# # 메트릭 정보 출력 함수
# def display_metrics(df, word_series):
#     top_word = word_series.idxmax()
#     top_word_count = word_series.max()
#     missing_data_count = df.shape[0]
#     completed_status_count = df[df['Status'] == '처리 완료'].shape[0]
#     completed_percentage = (completed_status_count / df.shape[0]) * 100

#     st.title("미응답 데이터 관리 페이지")
#     col1, col2, col3 = st.columns(3)
#     col1.metric("Most Common Word", f"{top_word}", f"{top_word_count} occurrences")
#     col2.metric("Missing Data Count", str(missing_data_count))
#     col3.metric("Completion Rate", f"{completed_percentage:.2f}%", "Percentage of completed status")

# # 그래프 출력 함수
# def plot_word_frequencies(word_series):
#     st.subheader("형태소 분석 결과 - Top 10 미응답 단어")
#     fig, ax = plt.subplots(figsize=(10, 6))
#     word_series.plot(kind='bar', color='skyblue', ax=ax)
#     ax.set_title('Top 10 Words by TF-IDF Score')
#     ax.set_xlabel('Words')
#     ax.set_ylabel('TF-IDF Score')
#     st.pyplot(fig)

# # 데이터 출력 함수
# def display_data_editor(df):
#     st.data_editor(df.reset_index(drop=True),
#                    hide_index=True,
#                    column_config={
#                        'QuestionID': st.column_config.Column(disabled=True),
#                        'QuestionText': st.column_config.Column(disabled=True),
#                        'Status': st.column_config.Column(disabled=False),
#                        'StatusUpdateDate': st.column_config.Column(disabled=True),
#                        'DownloadDate': st.column_config.Column(disabled=True),
#                        'CreateDate': st.column_config.Column(disabled=True)
#                    })

# # 전체 워크플로우 실행 함수
# def main(df, pecab):
#     word_series = process_texts(df, pecab)
#     display_metrics(df, word_series)
#     plot_word_frequencies(word_series)

#     items_per_page = 10
#     current_data, page, total_pages = paginate_data(df, items_per_page)
#     display_data_editor(current_data)
#     st.write(f"Page {page} of {total_pages}")

# main(df, pecab)

# import pandas as pd
# import streamlit as st

# # 데이터프레임 생성
# data_df = pd.DataFrame(
#     {
#         "widgets": ["st.selectbox", "st.number_input", "st.text_area", "st.button"],
#         "favorite": [True, False, False, True],
#     }
# )

# # 데이터 에디터 출력
# edited_data = st.data_editor(
#     data_df,
#     column_config={
#         "favorite": st.column_config.CheckboxColumn(
#             "Your favorite?",
#             help="Select your **favorite** widgets",
#             default=False,
#         )
#     },
#     disabled=["widgets"],
#     hide_index=True,
# )

# # 'favorite'가 True인 데이터만 필터링
# filtered_df = edited_data[edited_data['favorite'] == True]

# # CSV 파일로 저장하는 버튼 추가
# if not filtered_df.empty:
#     csv = filtered_df.to_csv(index=False)
#     st.download_button(
#         label="Download CSV",
#         data=csv,
#         file_name="favorite_widgets.csv",
#         mime="text/csv",
#     )
# else:
#     st.write("No favorite widgets selected.")