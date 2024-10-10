import streamlit as st
from menu import menu_with_redirect
import pandas as pd
import os
import sys
import io

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'server'))

from server import hana_cloud_service as hcs
from server import object_store_service as oss

menu_with_redirect()

st.markdown(""" 
    <style>
    .title {
        margin-bottom: -40px;
    }
    .divider {
        margin-top: 20px;
        margin-bottom: 70px;
    }
    .metrics {
        margin-top: 30px;
    }
    </style>
    """, unsafe_allow_html=True)

with st.container():
    st.markdown('<h2 class="title">매뉴얼 원본 데이터 관리 페이지</h2>', unsafe_allow_html=True)
    st.markdown('<hr class="divider">', unsafe_allow_html=True)

if "original_pdf_df" not in st.session_state:
    df = hcs.select_all_filenames_table()
    df = df.set_index("CodeID")
    df.columns = ["파일명", "생성날짜", "매뉴얼링크"]
    df["매뉴얼링크"] = oss.getUrl() + df["매뉴얼링크"]
    df["생성날짜"] = pd.to_datetime(df['생성날짜'], errors='coerce')

    st.session_state.original_pdf_df = df

# 데이터 페이지 나누기 함수
def split_frame(input_df, rows):
    return [input_df.iloc[i:i + rows] for i in range(0, len(input_df), rows)]

def removeData(selected_rows):
    drop_indexes = selected_rows.index.tolist()
    st.session_state.original_pdf_df = st.session_state.original_pdf_df.drop(drop_indexes)

    code_list = hcs.select_code_list(drop_indexes) 
    oss.delete_file_from_s3([code + '.pdf' for code in code_list])
    hcs.remove_selected_files(drop_indexes)

    child_pdf_list = hcs.select_child_pdf_list(code_list)
    oss.delete_file_from_s3(child_pdf_list)
    hcs.remove_child_files(code_list)

    delete_row_count = len(drop_indexes)
    st.toast(f"{delete_row_count}건의 파일이 삭제되었습니다.", icon="🗑️")

# Pagination
original_pdf_df = st.session_state.original_pdf_df

if original_pdf_df.empty: 
    st.info("저장된 매뉴얼이 없습니다. 매뉴얼을 업로드 해주세요", icon="ℹ️")
else: 
    col1, col2 = st.columns(2)

    with col1:
        period_filter = st.date_input("생성날짜", key="period_filter_1", value=None)  
    with col2:
        category_filter = st.selectbox("파일명", options=["전체"] + list(original_pdf_df['파일명'].unique()), key="category_filter_1")  

    has_filters = any([period_filter is not None, category_filter != "전체"])
    invalid_input = False

    if period_filter:
        valid_dates = original_pdf_df['생성날짜'].dt.date.tolist()
        if period_filter not in valid_dates:
            invalid_input = True

    if category_filter != "전체":
        valid_categories = original_pdf_df['파일명'].unique().tolist()
        if category_filter not in valid_categories:
            invalid_input = True

    filtered_df = original_pdf_df.copy()

    # Apply the filters if any filter is selected
    if has_filters:
        # Filter by period
        if period_filter is not None:
            filtered_df = filtered_df[filtered_df['생성날짜'].dt.date == period_filter]

        # Filter by category
        if category_filter != "전체":
            filtered_df = filtered_df[filtered_df['파일명'] == category_filter]

    # Check if filtered DataFrame is empty
    if filtered_df.empty:
        st.warning("선택하신 날짜의 데이터가 존재하지 않습니다.", icon="⚠️")
    else:
        # Page Size 설정
        top_menu = st.columns((3, 1, 1))
        with top_menu[2]:
            batch_size = st.selectbox("Page Size", options=["전체", 3, 5, 10, 20, 30, 40, 50], key="batch_size")

        # 페이지 나누기 처리
        if batch_size != "전체":
            batch_size = int(batch_size)
            pages = split_frame(filtered_df, batch_size)
            total_pages = len(pages)  # 전체 페이지 수 계산
            current_page = top_menu[1].number_input("Page", min_value=1, max_value=total_pages, value=1, step=1, key="current_page") if total_pages > 0 else 1
            display_df = pages[current_page - 1]  # 현재 페이지 데이터 표시
        else:
            display_df = filtered_df  # 전체 데이터를 표시
            total_pages = 1  # 전체 페이지 수를 1로 설정
            current_page = 1  # 현재 페이지 리셋

        # 페이지 정보 표시
        with top_menu[0]:
            st.markdown(f"Page **{current_page}** of **{total_pages}** ")
            #select_all_checkbox = st.checkbox("전체 선택", key="select_all")

        if not display_df.empty:
            edited_df = st.dataframe(
                display_df,
                column_config={
                    "파일명": st.column_config.TextColumn(disabled=True),
                    "생성날짜": st.column_config.DateColumn(disabled=True),
                    "매뉴얼링크": st.column_config.LinkColumn("매뉴얼 링크", display_text="상세보기", disabled=True)
                },
                use_container_width=True,
                on_select="rerun",
                selection_mode=["multi-row"],
                hide_index=True,
            )  
            selected_rows_indexs = edited_df.selection["rows"]
            selected_rows = display_df.iloc[selected_rows_indexs]

            btn_container = st.container()
            with btn_container:
                top_menu_empty = st.columns((3, 3, 2, 1))

                with top_menu_empty[3]:
                    delete_button = st.button(
                        label="삭제",
                        on_click=removeData,
                        kwargs={"selected_rows": selected_rows},
                        disabled=selected_rows.empty
                    )
        else:
            st.warning("해당 조건에 맞는 데이터가 없습니다.")
