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

st.selectbox(
        "Select your role:",
        ["사용자", "관리자"],
        key="_role",
        on_change=set_role,
    )

if st.session_state._role == "관리자" and not st.session_state.authenticated:
    st.text_input("관리자 비밀번호를 입력하세요",
                    placeholder="enter password..",
                    type="password",
                    key="admin_password")

    st.button("확인", on_click=check_admin_login)

if st.session_state.role=="관리자" and st.session_state.authenticated:
    #st.success("관리자 로그인에 성공했습니다. 좌측 상단의 [관리자] 선택이 가능합니다.", icon="✅")
    st.button(":material/Logout: logout", on_click=admin_logout, type="primary")