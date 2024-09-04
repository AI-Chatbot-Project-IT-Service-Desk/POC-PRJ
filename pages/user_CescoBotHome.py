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

st.title("CESCO AI CHATBOT")

if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "안녕하세요 세스코 서비스 데스크 AI 비서입니다. 무엇을 도와드릴까요?"}
    ]

# Function to display the chat history
def display_chat():
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):

            st.markdown(message["content"])

            if message.get("button"):
                st.download_button(label = message["button"]["label"],
                                   data = message["button"]["data"],
                                   file_name = message["button"]["file_name"],
                                   key = message["button"]["key"],
                                   mime='application/octet-stream')
            

            if message.get("button_group"):
                st.markdown("---")
                st.markdown("**이와 관련된 다른 질문들도 확인해보세요:**")
                    
                # button_cols = st.columns([2,2,2,2])
                # with button_cols[0]:
                #     st.button(label = message["button_group"]["r1"],
                #               key = message["button_group"]["r1_key"])
                # with button_cols[1]:
                #     st.button(label = message["button_group"]["r2"],
                #               key = message["button_group"]["r2_key"])
                # with button_cols[2]:
                #     st.button(label = message["button_group"]["r3"],
                #               key = message["button_group"]["r3_key"])
                # with button_cols[3]:
                #     st.button(label = message["button_group"]["r4"],
                #               key = message["button_group"]["r4_key"])
                    
                st.button(label = message["button_group"]["r1"],
                          key = message["button_group"]["r1_key"])
                st.button(label = message["button_group"]["r2"],
                          key = message["button_group"]["r2_key"])
                st.button(label = message["button_group"]["r3"],
                          key = message["button_group"]["r3_key"])
                st.button(label = message["button_group"]["r4"],
                          key = message["button_group"]["r4_key"])

# Display the chat history
display_chat()

# User input
if prompt := st.chat_input("Enter your question"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    #k1~k5
    df_context = hcs.run_vector_search(query=prompt, metric="L2DISTANCE", k=5)
    #k1
    df_context_k1 = df_context.iloc[0]
    #k1 답변
    response = hcs.ask_llm(query=prompt, k1_context=df_context_k1)
    #k2~k5 recommend
    recommend_group = {"r1": df_context.iloc[1]["ProblemDescription"], "r1_key": df_context.iloc[1]["SolutionDoc"],
                       "r2": df_context.iloc[2]["ProblemDescription"], "r2_key": df_context.iloc[2]["SolutionDoc"],
                       "r3": df_context.iloc[3]["ProblemDescription"], "r3_key": df_context.iloc[3]["SolutionDoc"],
                       "r4": df_context.iloc[4]["ProblemDescription"], "r4_key": df_context.iloc[4]["SolutionDoc"]}
    
    #매뉴얼 다운로드 버튼
    document_filecode = str(df_context_k1["SolutionDoc"])
    document_filename = str(df_context_k1["ProblemCategory"])
    opf = oss.open_pdf_file(document_filecode, document_filename)

    button_info = {"label": "매뉴얼 보기", "data": opf['data'], "file_name":opf['file_name'], "key":opf['file_name']}
    
    st.session_state.messages.append({
        "role": "assistant",
        "content": response,
        "button": button_info,
        "button_group": recommend_group
    })

    # Display the assistant's response
    with st.chat_message("assistant"):
        st.markdown(response)
        st.download_button(label= button_info["label"],
                           data = button_info["data"],
                           file_name = button_info["file_name"],
                           key = button_info["key"],
                           mime='application/octet-stream')       
        st.markdown("---")
        st.markdown("**이와 관련된 다른 질문들도 확인해보세요:**")
        # button_cols = st.columns([2,2,2,2])
        # with button_cols[0]:
        #     st.button(label=recommend_group["r1"],
        #               key=recommend_group["r1_key"])
        # with button_cols[1]:
        #     st.button(label=recommend_group["r2"],
        #               key=recommend_group["r2_key"])
        # with button_cols[2]:
        #     st.button(label=recommend_group["r3"],
        #               key=recommend_group["r3_key"])
        # with button_cols[3]:
        #     st.button(label=recommend_group["r4"],
        #               key=recommend_group["r4_key"])
            
        st.button(label = recommend_group["r1"],
                  key = recommend_group["r1_key"])
        st.button(label = recommend_group["r2"],
                  key = recommend_group["r2_key"])
        st.button(label = recommend_group["r3"],
                  key = recommend_group["r3_key"])
        st.button(label = recommend_group["r4"],
                  key = recommend_group["r4_key"])
        