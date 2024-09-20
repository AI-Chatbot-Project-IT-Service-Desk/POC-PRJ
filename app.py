import streamlit as st
from menu import menu

# Initialize st.session_state.role to "사용자"
if "role" not in st.session_state:
    st.session_state.role = "사용자"

# 관리자로서 로그인 인증을 완료했는지 여부
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

st.session_state._role = st.session_state.role

menu()

st.switch_page("pages/user_CescoBotHome.py")