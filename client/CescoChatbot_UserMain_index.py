import streamlit as st
import random
import time

# 비밀번호 설정
ADMIN_PASSWORD = "0000"  # 실제 비밀번호로 교체하세요

# Streamed response emulator
def response_welcome():
    return random.choice(
        [
            "안녕하세요, CESCO IT 헬프데스크 챗봇입니다 ✨ 전산 시스템 사용 중 궁금한 점이나 문제가 있다면 언제든지 질문해 주세요!",
            "안녕하세요, CESCO IT 헬프데스크 챗봇입니다 ✨ 궁금한 사항이 있으신가요? 필요한 정보를 빠르게 찾아드리겠습니다 :)",
        ]
    )

def response_generator():
    response = random.choice(
        [
            "Here is some information about your query.",
            "This is what I found related to your question.",
            "Here are the details you might find helpful.",
        ]
    )
    for word in response.split():
        yield word + " "
        time.sleep(0.05)

def main_page():
    # 초기화
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'auth_mode' not in st.session_state:
        st.session_state.auth_mode = False
    if 'welcome_shown' not in st.session_state:
        st.session_state.welcome_shown = False

    # 사이드바 메뉴 설정
    def get_pages():
        pages = {
            "🤖 CESCO BOT 🤖": [
                st.Page("CescoChatbot_UserMain_index.py", title="◽ Cesco-Bot Home"),
                st.Page("CescoChatbot_user.py", title="◽ Manual List"),
            ]
        }
        if st.session_state.authenticated:
            pages["🤖 CESCO BOT 🤖"].append(
                st.Page("CescoChatbot_RawManage.py", title="◽ Setting")
            )
        return pages

    # st.sidebar.title("관리자 모드")
    if not st.session_state.authenticated:
        if st.sidebar.button("관리자 모드"):
            st.session_state.auth_mode = True

    # 관리자 모드 비밀번호 입력                
    if st.session_state.auth_mode:
        password = st.sidebar.text_input("비밀번호를 입력하세요", type="password")
        if st.sidebar.button("확인"):
            if password == ADMIN_PASSWORD:
                st.session_state.authenticated = True
                st.session_state.auth_mode = False
                st.success("관리자 모드 활성화!")
                st.session_state.page_refresh = not st.session_state.get("page_refresh", False)
            else:
                st.sidebar.error("비밀번호가 틀렸습니다.")

    # 페이지 설정 및 실행
    pg = st.navigation(get_pages())
    pg.run()

    st.title("Cesco AI Chatbot")
    st.markdown("<hr style='border:1.5px solid #E0F7FA'>", unsafe_allow_html=True)

    # 채팅 기록 초기화
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # 환영 메시지를 처음 실행 시에만 메시지 히스토리에 추가
    if not st.session_state.welcome_shown:
        welcome_message = response_welcome()
        st.session_state.messages.append({"role": "assistant", "content": welcome_message})
        st.session_state.welcome_shown = True

    # 앱 재실행 시 채팅 기록에서 메시지 표시
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # 사용자 입력 받기
    if prompt := st.chat_input("What is up?"):
        # 사용자 메시지를 채팅 기록에 추가
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # 채팅 메시지 컨테이너에 사용자 메시지 표시
        with st.chat_message("user"):
            st.markdown(prompt)

        # 채팅 메시지 컨테이너에 어시스턴트 응답 표시
        with st.chat_message("assistant"):
            response_generator_obj = response_generator()
            response = ""
            for word in response_generator_obj:
                response += word
            st.markdown(response)
            
            # 문서 링크 추가
            st.write("**자세한 내용은 아래 링크를 클릭하여 확인해주세요!**")
            st.markdown("[🔗[링크] 메뉴얼 보기](https://docs.google.com/document/d/1uR5tDtUVeZtnn59WLAGuxe3IH2Ao3WeW773NzHn6huo/edit?usp=sharing)")

            # 사전 정의된 메시지에 대한 버튼 추가 (간격 조정)
            button_cols = st.columns([2, 2, 2, 2])  # 각 열의 비율을 작게 설정하여 간격 좁히기
            with button_cols[0]:
                if st.button("PDF 열람 방법이 궁금해요"):
                    st.session_state.messages.append({"role": "user", "content": "Hello!"})
            with button_cols[1]:
                if st.button("PDF 프로그램은 어떻게 설치해야 하나요?"):
                    st.session_state.messages.append({"role": "user", "content": "I need help."})
            with button_cols[2]:
                if st.button("PDF 열람 프로그램 사용시 계속 오류창이 발생해요"):
                    st.session_state.messages.append({"role": "user", "content": "Goodbye!"})
            with button_cols[3]:
                if st.button("PDF 문서를 보고싶은데, 어떻게 해야하나요?"):
                    st.session_state.messages.append({"role": "user", "content": "Thank you!"})

        # 어시스턴트 응답을 채팅 기록에 추가
        st.session_state.messages.append({"role": "assistant", "content": response})

if __name__ == '__main__':
    main_page()

# 스타일 적용
st.markdown(
    """
    <style>
    [data-testid="stSidebar"] {
        background-color:#E0F7FA; /* Light blue */
    }
    </style>
    """,
    unsafe_allow_html=True
)
