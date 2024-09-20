import streamlit as st
from importlib import import_module

# 관리자 비밀번호 설정
ADMIN_PASSWORD = "0000"  


def main():
    #사이드바 상단에 이미지 추가
    st.sidebar.image("path/to/your/image.png", use_column_width=True)

    # 세션 상태 초기화
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False

    # 사이드바에 카테고리별로 페이지 링크 추가
    category = st.sidebar.selectbox("카테고리", ["사용자 페이지", "관리자 페이지"])

    # 페이지 접근을 위한 비밀번호 입력 기능 추가
    if category == "관리자 페이지" and not st.session_state.authenticated:
        password = st.sidebar.text_input("비밀번호를 입력하세요", type="password")
        if st.sidebar.button("확인"):
            if password == ADMIN_PASSWORD:
                st.sidebar.success("비밀번호가 확인되었습니다.")
                st.session_state.authenticated = True
            else:
                st.sidebar.error("접속이 불가합니다.")

    # 각 카테고리별 페이지 선택 및 모듈 로드
    if st.session_state.authenticated or category == "사용자 페이지":
        if category == "사용자 페이지":
            page = st.sidebar.radio("페이지 선택", ["Cesco-Bot Home", "Manual List"])
            if page == "Cesco-Bot Home":
                module = import_module("pages.User_page.CescoBot_Home")
            elif page == "Manual List":
                module = import_module("pages.User_page.Manual_List")
        elif category == "관리자 페이지":
            page = st.sidebar.radio("페이지 선택", ["Cesco-Bot Home", "Manual List", "원본 데이터 관리", "QnA 데이터 관리", "무응답 데이터 관리"])
            if page == "Cesco-Bot Home":
                module = import_module("pages.User_page.CescoBot_Home")
            elif page == "Manual List":
                module = import_module("pages.User_page.Manual_List")
            elif page == "원본 데이터 관리":
                module = import_module("pages.Manager_page.RawManage")
            elif page == "QnA 데이터 관리":
                module = import_module("pages.Manager_page.QnAManage")
            elif page == "무응답 데이터 관리":
                module = import_module("pages.Manager_page.NoAnswer")

        # 모듈 실행
        module.run()
    else:
        st.warning("비밀번호를 입력하여 관리자 페이지에 접속하세요.")
        
    # 스타일 적용
        st.markdown(
            """
            <style>
            [data-testid="stSidebar"] {
            background-color:#e0f5ff; /* Light blue */
            }
            </style>
            """,
            unsafe_allow_html=True
        )

if __name__ == "__main__":
    main()