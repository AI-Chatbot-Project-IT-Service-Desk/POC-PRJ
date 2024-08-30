import os
import io
import streamlit as st
import json
import pandas as pd
import pecab
import hana_ml
from streamlit_pagination import pagination_component
from hana_ml import ConnectionContext
from hana_ml.dataframe import create_dataframe_from_pandas
from gen_ai_hub.proxy.native.openai import embeddings
from sklearn.feature_extraction.text import TfidfVectorizer
from collections import Counter
import matplotlib.pyplot as plt
import koreanize_matplotlib

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

column_mapping = {
    'QuestionID': '미응답 ID',
    'QuestionText': '미응답 내용',
    'Status': '처리 상태',
    'StatusUpdateDate': '질문 처리일',
    'DownloadDate': '다운로드 진행일',
    'CreateDate': '질문 생성일',
    # 추가적인 컬럼 이름 변경
}

st.markdown('<style>' + open(r'streamlit_pagination\style.css').read() + '</style>', unsafe_allow_html=True)

def data_chunk_choice():
    if 'foo' not in st.session_state or st.session_state['foo'] is None:
        return 0
    return st.session_state['foo']

n = 10
list_df = [df[i:i+n] for i in range(0,df.shape[0],n)]

layout = {
    'color': "primary",
    'style': {
        'margin-top': '10px',
        'display': 'flex',               # 데이터프레임 크기에 맞추기 위해 inline-flex 사용
        'justify-content': 'right',    # 수평 방향 가운데 정렬
    }
}

current_chunk = data_chunk_choice()
data = list_df[current_chunk]

if f'edited_data_{current_chunk}' in st.session_state:
    data = st.session_state[f'edited_data_{current_chunk}']
else:
    st.session_state[f'edited_data_{current_chunk}'] = data.copy()

def data_editor():
    st.title("미응답 테이블")
    df2 = st.data_editor(data.reset_index(drop=True), 
                        hide_index=True,
                        column_config={
                                        'QuestionID': st.column_config.Column(disabled=True),
                                        'QuestionText': st.column_config.Column(disabled=True),
                                        'Status': st.column_config.Column(disabled=False),
                                        'StatusUpdateDate': st.column_config.Column(disabled=True),
                                        'DownloadDate': st.column_config.Column(disabled=True),
                                        'CreateDate': st.column_config.Column(disabled=True)
                                    },
                        num_rows="dynamic"  # 행 추가 기능 비활성화
                        )
    if len(df2) > len(data):
        df2 = df2.iloc[:len(data)]
        st.warning("행 추가는 불가능합니다. 추가된 행이 삭제되었습니다.")
    
    st.session_state[f'edited_data_{current_chunk}'] = df2
    
    test = pagination_component(len(list_df) + 1, layout=layout, key="foo")

data_editor()