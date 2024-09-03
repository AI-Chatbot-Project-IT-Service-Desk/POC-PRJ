import streamlit as st
# from Pages.admin_Login import Login_Input

def user_menu():
    # Show a navigation menu for authenticated users
    st.sidebar.page_link("pages/user_CescoBotHome.py", label="🤖 채팅 시작하기")
    st.sidebar.page_link("pages/user_ManualList.py", label="📃 매뉴얼 열람하기")
    # CSS로 공백 추가
    st.sidebar.markdown(
        """
        <style>
        .spacer {
            height: 50vh;  /* 높이를 화면의 50%로 설정 */
        }
        </style>
        <div class="spacer"></div>
        """,
        unsafe_allow_html=True
)   
    # for _ in range(10):
    #     st.sidebar.empty()
    st.sidebar.markdown("----------------------")
    st.sidebar.page_link("pages/admin_Login.py", label="🔒 관리자 계정 로그인")

def admin_menu():
    #st.sidebar.page_link("pages/user_CescoBotHome.py", label="🤖 채팅 시작하기")
    #st.sidebar.page_link("pages/user_ManualList.py", label="📃 매뉴얼 열람하기")
    st.sidebar.page_link("pages/admin_UploadData.py", label="🗃️ 매뉴얼 업로드 페이지")
    st.sidebar.page_link("pages/admin_OriginDataManage2.py", label="📀 매뉴얼 원본 데이터 관리")
    st.sidebar.page_link("pages/admin_SplitDataManage.py", label="💿 매뉴얼 데이터 관리")
    st.sidebar.page_link("pages/admin_UnAnswerd.py", label="📊 미응답 데이터 관리")
    st.sidebar.markdown(
        """
        <style>
        .spacer {
            height: 50vh;  /* 높이를 화면의 50%로 설정 */
        }
        </style>
        <div class="spacer"></div>
        """,
        unsafe_allow_html=True
)   
    # for _ in range(10):
    #     st.sidebar.empty()
    st.sidebar.markdown("----------------------")
    st.sidebar.page_link("pages/admin_Login.py", label="🔒 사용자 돌아가기")


def set_role():
    # if st.session_state._role == "관리자":
    #     # Login_Input()
    #     if not st.session_state.authenticated:
    #     #     st.session_state._role = "사용자"
    #         st.toast("관리자 인증이 필요합니다", icon="⚠️")
    #     #     \return
        
    st.session_state.role = st.session_state._role

def select_role():
    st.selectbox(
        "Select your role:",
        ["사용자", "관리자"],
        key="_role",
        on_change=set_role,
    )

    #st.session_state.role = st.session_state._role

def menu():
    # select_role()
    if st.session_state.role == "사용자":
        user_menu()
    elif st.session_state.role == "관리자":
        if st.session_state.authenticated:
            admin_menu()
        else:
            user_menu()

def menu_with_redirect():
    if "role" not in st.session_state or st.session_state.role is None:
        st.switch_page("app2.py")

    st.session_state._role = st.session_state.role
    menu()