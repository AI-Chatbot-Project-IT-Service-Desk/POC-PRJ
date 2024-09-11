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

#[20240904 강태영] 미응답 질문 등록 버튼 key값
if "unanswered_num" not in st.session_state:
    st.session_state.unanswered_num = 0

#[20240909 강태영] 응답 질문 등록 버튼 key 값
if "answered_num" not in st.session_state:
    st.session_state.answered_num = 0

#[20240909 강태영] 재 질문 내용 담는 변수 
if "selected_question" not in st.session_state:
    st.session_state.selected_question = ""

def submit_recommended_question(question):
    st.session_state.selected_question = question
    print("메타몽2", st.session_state.selected_question)

# Function to display the chat history
def display_chat():
    st.empty()
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):

            st.markdown(message["content"])

            if message.get("button"):
                st.link_button(message["button"]["label"], message["button"]["s3_link"])
        
            if message.get("button_group"):
                st.markdown("---")
                st.markdown("**이와 관련된 다른 질문들도 확인해보세요:**")
                    
                st.button(label = message["button_group"]["r1"],
                          key = message["button_group"]["r1_key"],
                          on_click=submit_recommended_question,
                          kwargs={"question": message["button_group"]["r1"]})
                
                st.button(label = message["button_group"]["r2"],
                          key = message["button_group"]["r2_key"],
                          on_click=submit_recommended_question,
                          kwargs={"question": message["button_group"]["r2"]})
                
                st.button(label = message["button_group"]["r3"],
                          key = message["button_group"]["r3_key"],
                          on_click=submit_recommended_question,
                          kwargs={"question": message["button_group"]["r3"]})
                
                st.button(label = message["button_group"]["r4"],
                          key = message["button_group"]["r4_key"],
                          on_click=submit_recommended_question,
                          kwargs={"question": message["button_group"]["r4"]})
            
            if message.get("un_answer_button"):
                st.button(label = message["un_answer_button"]["label"],
                          key = message["un_answer_button"]["key"],
                          on_click = hcs.upload_unanswered_data(message["un_answer_button"]["data"]))

# Display the chat history
display_chat()

# User input
if prompt := st.chat_input("Enter your question") or st.session_state.selected_question :
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    #k1~k5
    df_context = hcs.run_vector_search(query=prompt, metric="L2DISTANCE", k=5)
    #k1
    df_context_k1 = df_context.iloc[0]

    print("[LOG] L2_DISTANCE SCORE: ", df_context_k1["L2D_SIM"])

    #[20240904 강태영] 미응답 분류 로직 추가
    if df_context_k1["L2D_SIM"] >= 0.5: #미응답 분류
        response = "해당 질문과 관련된 답변이 아직 준비되지 못했습니다."

        un_answer_button = {"label": "미응답 질문 등록", 
                            "key": "un" + str(st.session_state.unanswered_num),
                            "data": prompt}
        
        #key 등록 후 증가
        st.session_state.unanswered_num += 1
        
        st.session_state.messages.append({
            "role": "assistant",
            "content": response,
            "un_answer_button": un_answer_button
        }) 
        
        with st.chat_message("assistant"):
            st.markdown(response)
            st.button(  label = un_answer_button["label"],
                        key = un_answer_button["key"],
                        on_click = hcs.upload_unanswered_data(un_answer_button["data"]))
            
    else: #답변
        #k1 답변
        response = hcs.ask_llm(query=prompt, k1_context=df_context_k1)

        #k2~k5 recommend
        recommend_group = {"r1": df_context.iloc[1]["ProblemDescription"], "r1_key": st.session_state.answered_num,
                        "r2": df_context.iloc[2]["ProblemDescription"], "r2_key": st.session_state.answered_num+1,
                        "r3": df_context.iloc[3]["ProblemDescription"], "r3_key": st.session_state.answered_num+2,
                        "r4": df_context.iloc[4]["ProblemDescription"], "r4_key": st.session_state.answered_num+3}
        
        #key 조합 후 증가
        st.session_state.answered_num += 4
        
        #매뉴얼 다운로드 버튼
        document_filecode = str(df_context_k1["SolutionDoc"])
        document_filename = str(df_context_k1["ProblemCategory"])
        
        #object store s3 host url
        document_url = oss.geturl() + document_filecode
        button_info = {"label": "매뉴얼 보기", "s3_link": document_url}

        st.session_state.messages.append({
            "role": "assistant",
            "content": response,
            "button": button_info,
            "button_group": recommend_group 
        })

        # Display the assistant's response
        with st.chat_message("assistant"):
            st.markdown(response)

            st.link_button(button_info["label"], button_info["s3_link"])
                   
            st.markdown("---")
            st.markdown("**이와 관련된 다른 질문들도 확인해보세요:**")
                
            st.button(label = recommend_group["r1"], 
                      key = recommend_group["r1_key"],
                      on_click= submit_recommended_question,
                      kwargs={"question": recommend_group["r1"]})
            
            st.button(label = recommend_group["r2"],
                    key = recommend_group["r2_key"],
                    on_click=submit_recommended_question,
                    kwargs={"question": recommend_group["r2"]})
            
            st.button(label = recommend_group["r3"],
                    key = recommend_group["r3_key"],
                    on_click=submit_recommended_question,
                    kwargs={"question": recommend_group["r3"]})
            
            st.button(label = recommend_group["r4"],
                    key = recommend_group["r4_key"],
                    on_click=submit_recommended_question,
                    kwargs={"question": recommend_group["r4"]})

