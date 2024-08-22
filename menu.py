import streamlit as st

def authenticated_menu():
    # Show a navigation menu for authenticated users
    st.sidebar.page_link("pages/user_CescoBotHome.py", label="🤖 채팅 시작하기")
    st.sidebar.page_link("pages/user_ManualList.py", label="📃 매뉴얼 열람하기")
    if st.session_state.role == "관리자":
        st.sidebar.page_link("pages/admin_OriginDataManage.py", label="📀 매뉴얼 원본 데이터 관리")
        st.sidebar.page_link("pages/admin_SplitDataManage.py", label="💿 매뉴얼 데이터 관리",)
        st.sidebar.page_link("pages/admin_UnAnswerd.py", label="📊 미응답 데이터 관리")

def unauthenticated_menu():
    # Show a navigation menu for unauthenticated users
    st.sidebar.page_link("app2.py", label="관리자 계정 로그인")

def menu():
    # Determine if a user is logged in or not, then show the correct
    # navigation menu
    if "role" not in st.session_state or st.session_state.role is "사용자":
        unauthenticated_menu()
        return
    authenticated_menu()

def menu_with_redirect():
    # Redirect users to the main page if not logged in, otherwise continue to
    # render the navigation menu
    if "role" not in st.session_state or st.session_state.role is None:
        st.switch_page("app2.py")
    menu()