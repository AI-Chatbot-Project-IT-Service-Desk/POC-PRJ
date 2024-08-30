# # 필요한 라이브러리 설치
# !pip install konlpy
# !pip install scikit-learn
# !pip install pandas
# !pip install matplotlib

# 라이브러리 불러오기
import os
import time
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

start_time = time.time()
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
df = hdf.collect()
texts = df['QuestionText'].tolist()

# 형태소 분석기 초기화
okt = Okt()

# 텍스트를 형태소로 분석하여 명사만 추출
tokenized_texts = [' '.join(okt.nouns(text)) for text in texts]

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
print(most_common_words)

# Pandas Series로 변환
word_series = pd.Series(dict(most_common_words))

print(word_series)

end_time = time.time()
print(f"Execution Time: {end_time - start_time} seconds")

# 그래프로 출력
# plt.figure(figsize=(10, 6))
# word_series.plot(kind='bar')
# plt.title('Top 10 Most Frequent Words')
# plt.xlabel('Words')
# plt.ylabel('Frequency')
# plt.xticks(rotation=45)
# plt.show()
