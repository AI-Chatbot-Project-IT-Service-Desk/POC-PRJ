import streamlit as st
from menu import menu_with_redirect
from menu import menu
from menu import select_role

# Redirect to app.py if not logged in, otherwise show the navigation menu
menu_with_redirect()
select_role()

ADMIN_PASSWORD = "0000"

def check_admin_login(admin_password):
    if admin_password: 
        if admin_password == ADMIN_PASSWORD:
            st.session_state.authenticated = True
            st.toast("관리자 인증 완료", icon="✅")
        else:
            st.toast("올바르지 않은 비밀번호입니다.", icon="❌")
    
    admin_password = False
    
# def Login_Input():

if st.session_state._role == "관리자": 
    admin_password = st.text_input("관리자 비밀번호를 입력하세요",
                                    placeholder="enter password..",
                                    type="password")
    st.button("확인", on_click=check_admin_login(admin_password))

if st.session_state.authenticated:
    st.success("관리자 로그인에 성공했습니다. 좌측 상단의 [관리자] 선택이 가능합니다.", icon="✅")