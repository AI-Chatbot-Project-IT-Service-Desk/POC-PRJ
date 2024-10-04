import streamlit as st
from PIL import Image
import os
import sys
# from Pages.admin_Login import Login_Input

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '.', 'server'))

from server import object_store_service as oss
#image = Image.open(r"C:\Users\안성은\Desktop\SeongeunWorkspace\POC-PRJ\sidebar_image.png")
image = oss.getResources()

def user_menu():
    st.sidebar.image(image + 'sidebar_image.png', width=265)
    st.sidebar.markdown("----------------------")
    st.sidebar.page_link("pages/user_CescoBotHome.py", label=":material/Smart_Toy: 채팅 시작하기")
    st.sidebar.page_link("pages/user_ManualList.py", label=":material/Lists: 매뉴얼 열람하기")
    st.sidebar.markdown("----------------------")
    st.sidebar.page_link("pages/admin_Setting.py", label=":material/Settings: 설정")
    # 이미지 full screen 기능 버튼 숨기기
    hide_fullscreen_button = """
    <style>
    button[title="View fullscreen"] {
    display: none;
    }
    </style>
    """
    st.markdown(hide_fullscreen_button, unsafe_allow_html=True)

def admin_menu():
    st.sidebar.image(image + 'sidebar_image.png', width=265)
    st.sidebar.markdown("----------------------")
    st.sidebar.page_link("pages/admin_UploadData.py", label=":material/Upload_File: 매뉴얼 업로드 페이지")
    st.sidebar.page_link("pages/admin_OriginDataManage.py", label=":material/Folder_Managed: 매뉴얼 원본 데이터 관리")
    st.sidebar.page_link("pages/admin_SplitDataManage_filter.py", label=":material/Folder: 매뉴얼 데이터 관리",)
    st.sidebar.page_link("pages/admin_UnAnswerd.py", label=":material/Analytics: 무응답 데이터 관리")
    st.sidebar.markdown("----------------------")
    st.sidebar.page_link("pages/admin_Setting.py", label=":material/Settings: 설정")
    # 이미지 full screen 기능 버튼 숨기기
    hide_fullscreen_button = """
    <style>
    button[title="View fullscreen"] {
    display: none;
    }
    </style>
    """
    st.markdown(hide_fullscreen_button, unsafe_allow_html=True)

    #st.session_state.role = st.session_state._role

def menu():
    if st.session_state.role == "관리자":
        if st.session_state.authenticated:
            admin_menu()
        else:
            user_menu()
    elif st.session_state.role == "사용자":
        user_menu()

def menu_with_redirect():
    if "role" not in st.session_state or st.session_state.role is None:
        st.switch_page("app.py")

    st.session_state._role = st.session_state.role
    menu()