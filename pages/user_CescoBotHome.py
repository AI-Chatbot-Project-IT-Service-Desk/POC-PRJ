import streamlit as st
from menu import menu_with_redirect
import os
import sys

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'server'))
#print("경로 확인", os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'server'))

from server import object_store_service as oss
from server import hana_cloud_service as hcs
from server import pdf_split as ps

# Redirect to app.py if not logged in, otherwise show the navigation menu
menu_with_redirect()

st.title("CESCO AI Chatbot")

if "messages" not in st.session_state.keys():
    st.session_state.messages = [
        {"role": "assistant", "content": "안녕하세요 세스코 서비스 데스크 AI 비서입니다. 무엇을 도와드릴까요?"}
    ]

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Enter your question"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

#[20240902 강태영] 채팅 로직
if st.session_state.messages[-1]["role"] != "assistant":
    with st.chat_message("assistant"):
        placeholder = st.empty() 
        with st.spinner("처리 중입니다. 잠시만 기다려주세요"):
            # k1 ~ k5
            df_context = hcs.run_vector_search(query=prompt, metric="L2DISTANCE", k=5)
            print(df_context)
            # k1
            df_context_k1 = df_context.iloc[0]
            print(df_context_k1)
            response = hcs.ask_llm(query=prompt, k1_context=df_context_k1)
            placeholder.markdown(response)

            #매뉴얼 다운로드 버튼
            document_filecode = str(df_context_k1["SolutionDoc"])
            document_filename = str(df_context_k1["ProblemCategory"])
            opf = oss.open_pdf_file(document_filecode, document_filename)
            st.download_button(label="매뉴얼 보기",
                               data=opf['data'],
                               file_name=opf['file_name'],
                               mime='application/octet-stream')
            
    if response is not None:
            message = {"role": "assistant", "content": response}
            st.session_state.messages.append(message)