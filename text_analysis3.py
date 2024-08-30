'''
작성일: 2024-08-21
설명: 미응답 로직 테스트 파일
'''
import os
import json
import pandas as pd
import hana_ml
from hana_ml import ConnectionContext
from hana_ml.dataframe import create_dataframe_from_pandas
from gen_ai_hub.proxy.native.openai import embeddings
from konlpy.tag import Okt
from sklearn.feature_extraction.text import TfidfVectorizer
from collections import Counter
import matplotlib.pyplot as plt
import koreanize_matplotlib

# CESCO_UNANSWEREDQUESTIONS Table Select 함수
# def get_unanswerd_questions_data():
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

sql = '''SELECT * FROM "CESCO_UNANSWEREDQUESTIONS"'''
hdf = cc.sql(sql)
df_result = hdf.collect()
df = pd.DataFrame(df_result)

print(df)

text_column = 'QuestionText'
okt = Okt()
df['nouns'] = df[text_column].apply(lambda x: okt.nouns(x))
df['nouns_str'] = df['nouns'].apply(lambda x: ' '.join(x))

stopwords = ['의', '가', '이', '은', '는', '을', '를', '에', '와', '과', '로', '으로', '에서', '에게', '한', '하다']
tfidf_vectorizer = TfidfVectorizer(stop_words=stopwords, max_features=100)
tfidf_matrix = tfidf_vectorizer.fit_transform(df['nouns_str'])
tfidf_df = pd.DataFrame(tfidf_matrix.toarray(), columns=tfidf_vectorizer.get_feature_names_out())
threshold = 0.5
filtered_tfidf_df = tfidf_df.loc[:, (tfidf_df > threshold).any(axis=0)]

# 각 단어의 합계를 계산하여 빈도수 구하기
word_freq = filtered_tfidf_df.sum(axis=0)

# 상위 10개의 단어를 추출
top_words = word_freq.nlargest(10)
print(top_words)

# # 상위 단어들을 막대 그래프로 시각화
# plt.figure(figsize=(10, 6))
# top_words.plot(kind='bar', color='skyblue')
# plt.title('Top 10 Words by TF-IDF Score')
# plt.xlabel('Words')
# plt.ylabel('TF-IDF Score')
# plt.show()


    # hdf = cc.sql(sql)
    # df_result = hdf.collect()
    # df = pd.read_sql_query(sql, hdf)
    # print(df)

#실행
# get_unanswerd_questions_data()

# # 형태소 분석기 초기화
# okt = Okt()

# # 텍스트를 형태소로 분석하여 명사만 추출
# tokenized_texts = [' '.join(okt.nouns(text)) for text in texts]

# # TF-IDF를 사용하여 불용어 제거
# tfidf = TfidfVectorizer(min_df=1, max_df=0.5)  # max_df=0.5는 TF-IDF 점수가 높은 단어들만 포함
# tfidf_matrix = tfidf.fit_transform(tokenized_texts)
# feature_names = tfidf.get_feature_names_out()

# # TF-IDF 값이 0 이상인 단어들만 추출
# filtered_words = []
# for doc_idx in range(tfidf_matrix.shape[0]):
#     for word_idx, score in zip(tfidf_matrix[doc_idx].indices, tfidf_matrix[doc_idx].data):
#         if score > 0:
#             filtered_words.append(feature_names[word_idx])

# # 필터링된 단어의 빈도수 계산
# word_count = Counter(filtered_words)

# # 빈도수 상위 10개 단어 출력
# most_common_words = word_count.most_common(10)
# print(most_common_words)

# # Pandas Series로 변환
# word_series = pd.Series(dict(most_common_words))

# # 그래프로 출력
# plt.figure(figsize=(10, 6))
# word_series.plot(kind='bar')
# plt.title('Top 10 Most Frequent Words')
# plt.xlabel('Words')
# plt.ylabel('Frequency')
# plt.xticks(rotation=45)
# plt.show()
