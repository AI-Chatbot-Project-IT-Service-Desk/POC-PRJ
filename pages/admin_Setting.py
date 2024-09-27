import streamlit as st
from menu import menu_with_redirect
from menu import menu

# Redirect to app.py if not logged in, otherwise show the navigation menu
menu_with_redirect()

ADMIN_PASSWORD = "0000"

def set_role():
    st.session_state.role = st.session_state._role

def check_admin_login():
    if st.session_state.admin_password == ADMIN_PASSWORD:
        st.session_state.authenticated = True
        st.toast("관리자 인증 완료", icon="✅")
    else:
        st.toast("올바르지 않은 비밀번호입니다.", icon="❌")

def admin_logout():
    st.session_state.authenticated = False
    st.session_state.role = "사용자"
    #[20240912 강태영 로그아웃 버튼 누를시 챗팅 창 초기화]
    #전체 초기화
    st.session_state.clear()
    #챗팅창만 초기화
    # if 'messages' in st.session_state:
    #     st.session_state.messages = []

st.selectbox(
        "Select your role:",
        ["사용자", "관리자"],
        key="_role",
        on_change=set_role
)

if st.session_state._role == "관리자" and not st.session_state.authenticated:
    pass_word = st.text_input("관리자 비밀번호를 입력하세요",
                    placeholder="enter password..",
                    type="password",
                    key="admin_password",
                    on_change=check_admin_login)

    st.button("확인", on_click=check_admin_login)

if st.session_state.role=="관리자" and st.session_state.authenticated:
    st.button(":material/Logout: logout", on_click=admin_logout, type="primary")