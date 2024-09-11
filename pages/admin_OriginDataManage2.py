import streamlit as st
from menu import menu_with_redirect
import pandas as pd
import os
import sys
import io

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'server'))

from server import hana_cloud_service as hcs
from server import object_store_service as oss

# Redirect to app.py if not logged in, otherwise show the navigation menu
menu_with_redirect()

st.title("매뉴얼 원본 데이터 관리 페이지")

# 첫 데이터 프레임
if "original_pdf_df" not in st.session_state:
    df = hcs.select_all_filenames_table()
    df = df.set_index("CodeID")
    # DataFrame 이름 지정
    df.columns = ["파일명", "생성날짜", "매뉴얼링크"]
    #[20240911 강태영] s3 link url 붙이기
    df["매뉴얼링크"] = oss.getUrl() + df["매뉴얼링크"]
    # '생성날짜' 컬럼을 datetime 형식으로 변환
    df["생성날짜"] = pd.to_datetime(df['생성날짜'], errors='coerce')

    st.session_state.original_pdf_df = df

def removeData(selected_rows):
    #Index 객체에서 index 배열 추출.
    drop_indexes = selected_rows.index.tolist()
    #print(drop_indexes) #[2,3]

    #프론트 단에서 삭제
    st.session_state.original_pdf_df = st.session_state.original_pdf_df.drop(drop_indexes)

    #Object S3 삭제
    #CodeID 로 삭제할 Code(PDF) Select
    code_list = hcs.select_code_list(drop_indexes) #["cesco2", "cesco3"]
    oss.delete_file_from_s3([code + '.pdf' for code in code_list]) #["cesco2.pdf", "cesco3.pdf"]

    #DB 삭제
    hcs.remove_selected_files(drop_indexes)

    #Object S3 자식 파일 삭제
    #code_list로 묶여있는 자식 파일 찾아오기
    child_pdf_list = hcs.select_child_pdf_list(code_list)
    oss.delete_file_from_s3(child_pdf_list)

    #DB 자식 파일 삭제
    hcs.remove_child_files(code_list)

    #파일 삭제 알림
    delete_row_count = len(drop_indexes)
    st.toast(f"{delete_row_count}건의 파일이 삭제되었습니다.", icon="🗑️")


original_pdf_df = st.session_state.original_pdf_df

#[20240911 강태영] 데이터 프레임에 데이터가 있는지 확인
if original_pdf_df.empty: 
    st.info("저장된 매뉴얼이 없습니다. 매뉴얼을 업로드 해주세요", icon="ℹ️")
else: 
    # 사용자 입력 필터
    col1, col2 = st.columns(2)

    with col1:
        period_filter = st.date_input("생성날짜", key="period_filter_1", value=None)  # 고유한 키 사용
    with col2:
        category_filter = st.selectbox("카테고리", options=["전체"] + list(original_pdf_df['파일명'].unique()), key="category_filter_1")  # 고유한 키 사용

    # 필터 조건 확인
    has_filters = any([
        period_filter is not None,
        category_filter != "전체"
    ])

    # 유효성 검사 및 필터 적용
    invalid_input = False
    if period_filter:
        valid_dates = original_pdf_df['생성날짜'].dt.date.tolist()
        if period_filter not in valid_dates:
            invalid_input = True

    if category_filter != "전체":
        valid_categories = original_pdf_df['파일명'].unique().tolist()
        if category_filter not in valid_categories:
            invalid_input = True

    if invalid_input and has_filters:
        st.error("선택하신 날짜의 문서가 존재하지 않습니다.")
    else:
        # 필터 적용
        filtered_df = original_pdf_df.copy()  # 필터링 전 전체 데이터를 기본으로 표시

        if period_filter:
            filtered_df = filtered_df[filtered_df['생성날짜'].dt.date == period_filter]
        if category_filter != "전체":
            filtered_df = filtered_df[filtered_df['파일명'] == category_filter]
        
        # 페이지네이션을 위한 설정
        pagination = st.container()

        # 버튼 클릭 시 페이지 업데이트
        if 'current_page' not in st.session_state:
            st.session_state.current_page = 1
        
        top_menu = st.columns((3, 1, 1))
        
        with top_menu[2]:
            batch_size = st.selectbox("Page Size", options=[5, 10, 20, 30, 40, 50], key="batch_size")
        with top_menu[1]:
            total_pages = ((len(filtered_df) // batch_size) + (1 if len(filtered_df) % batch_size > 0 else 0))
            current_page = st.number_input("Page", min_value=1, max_value=total_pages, step=1, key="current_page")
        with top_menu[0]:
            st.markdown(f"Page **{st.session_state.current_page}** of **{total_pages}** ")

        # 데이터 페이지 나누기
        def split_frame(input_df, rows):
            return [input_df.iloc[i:i + rows] for i in range(0, len(input_df), rows)]
        
        pages = split_frame(filtered_df, batch_size)
        if total_pages > 0:
            # st.data_editor를 사용하여 체크박스를 포함한 데이터 표시
            edited_df = st.dataframe(
                pages[st.session_state.current_page - 1],
                column_config={
                    #"선택": st.column_config.CheckboxColumn(),  # 체크박스는 수정 가능
                    "파일명": st.column_config.TextColumn(disabled=True),  # 수정 불가
                    "생성날짜": st.column_config.DateColumn(disabled=True),  # 수정 불가
                    "매뉴얼링크": st.column_config.LinkColumn("매뉴얼 링크", 
                                                        display_text="상세보기",
                                                        disabled=True)  # 수정 불가
                    },
                use_container_width=True,
                on_select="rerun",
                selection_mode=["multi-row"],
                hide_index=True,
            )
            
            # 체크박스를 선택한 항목만 다운로드 및 삭제 기능
            #selected_rows = edited_df[edited_df['선택'] == True]
            selected_rows_indexs = edited_df.selection["rows"]
            selected_rows = pages[st.session_state.current_page - 1].iloc[selected_rows_indexs]

            # 버튼을 배치할 빈 컨테이너
            btn_container = st.container()
            with btn_container:
                # 빈 공간을 만들기 위한 두 개의 빈 열
                top_menu_empty = st.columns((3, 3, 2, 1))

            #     # 다운로드 링크 생성 함수
            #     with top_menu_empty[2]:
            #         def create_download_link(df, file_name):
            #             buffer = io.StringIO()
            #             df.to_csv(buffer, index=False)
            #             buffer.seek(0)
            #             return st.download_button(
            #                 label="매뉴얼 다운로드",
            #                 data=buffer.getvalue(),
            #                 file_name=file_name,
            #                 mime="text/csv",
            #                 disabled=df.empty  # 선택된 항목이 없을 경우 버튼 비활성화
            #             )
                    # '매뉴얼 다운로드' 버튼을 항상 표시
                    #create_download_link(selected_rows, "selected_data.csv")

                # 삭제 버튼
                with top_menu_empty[3]:
                    delete_button = st.button(
                    label="삭제",
                    on_click=removeData,
                    kwargs={"selected_rows" : selected_rows},
                    disabled = selected_rows.empty # 선택된 항목이 없으면 비활성화
                )

                #     if delete_button and not selected_rows.empty:
                #         # 선택된 파일 삭제 처리 로직 (예: DB에서 삭제)
                #         for index, row in selected_rows.iterrows():
                #             # 여기에 실제 삭제 로직 구현 (DB에서 삭제 등)
                #             st.write(f"{row['파일명']} 파일을 삭제합니다.")
                        
                #         # 삭제가 완료되면 페이지를 다시 로드하여 데이터 갱신
                #         st.session_state.reload = True
                
        else:
            st.warning("해당 조건에 맞는 데이터가 없습니다.")

# 페이지가 새로고침 될 때
# if 'reload' in st.session_state and st.session_state.reload:
#     st.session_state.reload = False
#     st.experimental_rerun()

