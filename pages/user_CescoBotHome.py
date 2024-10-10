import streamlit as st
from menu import menu_with_redirect
import os
import sys

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'server'))
#print("경로 확인", os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'server'))

from server import object_store_service as oss
from server import hana_cloud_service as hcs
from server import pdf_split as ps

# CSS 스타일 적용 (버튼 텍스트를 왼쪽 정렬)
st.markdown("""
            <style>
            .stButton button {
            text-align: left;
            width: 100%;
            display: flex;
            justify-content: flex-start;
            background-color: #fafafa;  /* 옅은 회색 */
            color: black;  
            }

            .stButton button[kind="primary"] {
                border: 1px solid rgb(210 210 213);
                background: none;
                outline: none;
            }

            .stButton button[kind="primary"]:hover {
                color: #ff2b2b;
                border: 1px solid #ff2b2b;
            }
            </style>
            """, unsafe_allow_html=True)

# Redirect to app.py if not logged in, otherwise show the navigation menu
menu_with_redirect()

st.title("CESCO AI CHATBOT")

if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "안녕하세요 세스코 서비스 데스크 AI 비서입니다. 무엇을 도와드릴까요?"}
    ]

#[20240904 강태영] 무응답 질문 등록 버튼 key값
if "unanswered_num" not in st.session_state:
    st.session_state.unanswered_num = 0

#[20240909 강태영] 응답 질문 등록 버튼 key 값
if "answered_num" not in st.session_state:
    st.session_state.answered_num = 0

#[20240909 강태영] 재 질문 내용 담는 변수 
if "selected_question" not in st.session_state:
    st.session_state.selected_question = ""

# [20240925 강태영] 그룹 상태 관리
if "group_states" not in st.session_state:
    st.session_state.group_states = {}

def submit_recommended_question(question):
    st.session_state.selected_question = question

#[20240911 강태영] 무응답 버튼 클릭시 evnet 묶음
def handle_unanswered_click_event(unquestion):
    if hcs.upload_unanswered_data(unquestion):
        st.toast("질문이 등록 되었습니다.", icon="🥳")
    else:
        st.toast("이미 등록된 질문입니다", icon="😊")

#[20240925 강태영] 닫기 버튼 클릭시 event
def handle_closed_button(group_name):
    if st.session_state.group_states[group_name]:
        st.session_state.group_states[group_name] = False
    else:
        st.session_state.group_states[group_name] = True

# Function to display the chat history
def display_chat():
    st.empty()
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):

            st.markdown(message["content"])

            if message.get("button"):
                st.link_button(message["button"]["label"], message["button"]["s3_link"])
        
            if message.get("un_answer_button"):
                st.button(label = message["un_answer_button"]["label"],
                          key = message["un_answer_button"]["key"],
                          on_click = handle_unanswered_click_event,
                          kwargs={"unquestion": message["un_answer_button"]["data"]})
                
            if message.get("button_group"):
                group_name = message.get("group_name")
                st.markdown("---")
                
                label_message = ":material/Close: 질문 닫기"

                if st.session_state.group_states[group_name]:
                    st.button(label=label_message, type="primary",
                            key=f"cancelbt_{message["button_group"]["r1_key"]}",
                            on_click = handle_closed_button, 
                            kwargs={"group_name": group_name})

                    with st.container(border=True):
                            
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
                else:
                    if message.get("un_answer_button"):
                        label_message = ":material/Arrow_Forward_iOS: 이렇게 질문해보는 건 어떠세요?"
                    else:
                        label_message = ":material/Arrow_Forward_iOS: 이와 관련된 다른 질문들도 확인해보세요!"

                    st.button(label=label_message, type="primary",
                            key=f"cancelbt_{message["button_group"]["r1_key"]}",
                            on_click = handle_closed_button, 
                            kwargs={"group_name": group_name})        

# Display the chat history
display_chat()

# User input
if prompt := st.chat_input("Enter your question") or st.session_state.selected_question :
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        placeholder = st.empty()    
        with st.spinner("메시지 처리 중입니다. 잠시만 기다려주세요"):
            #k1~k5
            df_context = hcs.run_vector_search(query=prompt, metric="L2DISTANCE", k=5)
            #k1
            df_context_k1 = df_context.iloc[0]

            print("[LOG] L2_DISTANCE SCORE: ", df_context_k1["L2D_SIM"])

            #[20240904 강태영] 무응답 분류 로직 추가
            if df_context_k1["L2D_SIM"] >= 0.5: #무응답 분류
                response = "해당 질문과 관련된 답변이 아직 준비되지 못했습니다."

                un_answer_button = {"label": "⚠️ 무응답 질문 등록", 
                                    "key": "un" + str(st.session_state.unanswered_num),
                                    "data": prompt}
                
                #k1~k4 recommend
                recommend_group_name = f"group_{st.session_state.answered_num}"
                recommend_group = {"r1": df_context.iloc[0]["ProblemDescription"], "r1_key": st.session_state.answered_num,
                                "r2": df_context.iloc[1]["ProblemDescription"], "r2_key": st.session_state.answered_num+1,
                                "r3": df_context.iloc[2]["ProblemDescription"], "r3_key": st.session_state.answered_num+2,
                                "r4": df_context.iloc[3]["ProblemDescription"], "r4_key": st.session_state.answered_num+3}
                #key 등록 후 증가
                st.session_state.unanswered_num += 1
                st.session_state.answered_num += 4
                
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": response,
                    "un_answer_button": un_answer_button,
                    "button_group": recommend_group, 
                    "group_name": recommend_group_name
                }) 

                st.session_state.group_states[recommend_group_name] = False
                
                with placeholder.container():
                    st.markdown(response)
                    st.button(  label = un_answer_button["label"],
                                key = un_answer_button["key"],
                                on_click = handle_unanswered_click_event,
                                kwargs={"unquestion": un_answer_button["data"]})
                    
                    st.markdown("---")
                    st.button(label=":material/Arrow_Forward_iOS: 이렇게 질문해보는 건 어떠세요?", type="primary",
                                key=f"cancelbt_{recommend_group["r1_key"]}",
                                on_click = handle_closed_button, 
                                kwargs={"group_name": recommend_group_name})                    
                            
            else: #답변
                #k1 답변
                response = hcs.ask_llm(query=prompt, k1_context=df_context_k1)

                #k2~k5 recommend
                recommend_group_name = f"group_{st.session_state.answered_num}"
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
                document_url = oss.getUrl() + document_filecode
                button_info = {"label": "매뉴얼 확인하기", "s3_link": document_url}

                st.session_state.messages.append({
                    "role": "assistant",
                    "content": response,
                    "button": button_info,
                    "button_group": recommend_group,
                    "group_name": recommend_group_name 
                })

                st.session_state.group_states[recommend_group_name] = False

                # Display the assistant's response
                with placeholder.container():
                    st.markdown(response)
                    st.link_button(button_info["label"], button_info["s3_link"])
                        
                    st.markdown("---")
                    st.button(label=":material/Arrow_Forward_iOS: 이와 관련된 다른 질문들도 확인해보세요!", type="primary",
                                key=f"cancelbt_{recommend_group["r1_key"]}",
                                on_click = handle_closed_button, 
                                kwargs={"group_name": recommend_group_name})
            
#[20240912 강태영] 다 하고 나서 초기화 하기
st.session_state.selected_question = ""

