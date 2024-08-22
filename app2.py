import streamlit as st
from menu import menu

# Initialize st.session_state.role to None
if "role" not in st.session_state:
    st.session_state.role = "사용자"

# 관리자로서 로그인 인증을 완료했는지 여부
if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False

# Retrieve the role from Session State to initialize the widget
st.session_state._role = st.session_state.role

# 관리자 비밀번호 설정
ADMIN_PASSWORD = "0000"  

def set_role():
    st.session_state.role = st.session_state._role
    

#Selectbox to choose role
st.sidebar.selectbox(
    "Select your role", 
    ["사용자", "관리자"],
    key="_role",
    on_change=set_role
)
menu()