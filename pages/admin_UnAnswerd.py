import os
import io
import sys
import streamlit as st
import pandas as pd
import pecab
import matplotlib.pyplot as plt
from matplotlib import font_manager, rc
from collections import Counter
from sklearn.feature_extraction.text import TfidfVectorizer

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'server'))
from server import hana_cloud_service as hcs
from menu import menu_with_redirect

menu_with_redirect()

pecab = pecab.PeCab()

# [20240912 강태영] 삭제를 위해 dataframe을 session_state에 넣는다
if "unanswered_df" not in st.session_state:
    df = hcs.select_all_unansweredquestions_table()
    df = df.set_index("QuestionID")
    df.columns = ['생성날짜', '처리날짜', '미응답 내용', '처리상태']
    df['생성날짜'] = pd.to_datetime(df['생성날짜'], errors='coerce')
    df['처리날짜'] = pd.to_datetime(df['처리날짜'], errors='coerce')
    df.insert(0, "선택", False)

    st.session_state.unanswered_df = df

texts = st.session_state.unanswered_df['미응답 내용'].tolist()

# Analyze and visualize texts
def analyze_texts(texts, pecab, top_n=10):
    font_path = 'fonts\세스코R_20140905153946.TTF'  # 서버에 맞는 폰트 경로 설정
    font = font_manager.FontProperties(fname=font_path).get_name()
    rc('font', family=font)

    tokenized_texts = [' '.join([word for word, pos in pecab.pos(text) if pos in ['NNG', 'NNP']]) for text in texts]
    tfidf = TfidfVectorizer(min_df=1, max_df=0.5)
    tfidf_matrix = tfidf.fit_transform(tokenized_texts)
    feature_names = tfidf.get_feature_names_out()

    words = [feature_names[word_idx] for doc_idx in range(tfidf_matrix.shape[0])
             for word_idx, score in zip(tfidf_matrix[doc_idx].indices, tfidf_matrix[doc_idx].data) if score > 0]
    word_count = Counter(words).most_common(top_n)
    
    word_series = pd.Series(dict(word_count))
    
    fig, ax = plt.subplots(figsize=(10, 6))
    word_series.plot(kind='bar', color='skyblue', ax=ax)
    ax.set_title(f'Top {top_n} Words')
    ax.set_xlabel('단어')
    plt.xticks(rotation=0)
    ax.set_ylabel('빈도 수')
    st.pyplot(fig)
    
    return word_series

# Display dashboard
def display_dashboard(word_series, unanswered_df, status_column='처리상태', completed_value='처리 완료'):
    col1, col2, col3 = st.columns(3)
    top_word, top_word_count = word_series.idxmax(), word_series.max()
    completed_count = unanswered_df[unanswered_df[status_column] == completed_value].shape[0]
    
    col1.metric("Most Common Word", top_word, f"{top_word_count} occurrences")
    col2.metric("Missing Data Count", unanswered_df.shape[0])
    col3.metric("Completion Rate", f"{(completed_count / unanswered_df.shape[0]) * 100:.2f}%")

# Filter Data
def filter_data(unanswered_df, period_filter=None, period_filter2=None, category_filter="전체"):
    original_df = unanswered_df.copy()  # 원본 유지
    if period_filter:
        unanswered_df = unanswered_df[unanswered_df['생성날짜'].dt.date == period_filter]
    if period_filter2:
        unanswered_df = unanswered_df[unanswered_df['처리날짜'].dt.date == period_filter2]
    if category_filter != "전체":
        unanswered_df = unanswered_df[unanswered_df['미응답 내용'] == category_filter]

    # 데이터가 없으면 문구 출력
    if unanswered_df.empty and not original_df.empty:
        return unanswered_df, True
    return unanswered_df, False

# Pagination
def paginate_data(filtered_df, batch_size, current_page):
    pages = [filtered_df.iloc[i:i + batch_size] for i in range(0, len(filtered_df), batch_size)]
    return pages[current_page - 1] if pages else None

# Download CSV
def create_download_link(df, file_name):
    # Remove the checkbox column before saving to CSV
    df_to_save = df.drop(columns=['선택'], errors='ignore')
    buffer = io.BytesIO()
    df_to_save.to_csv(buffer, index=False, encoding='utf-8-sig')
    buffer.seek(0)
    return buffer.getvalue()

# [20240912 강태영] 삭제 함수
def removeData(selected_rows):
    drop_indexes = selected_rows.index.tolist()
    #프론트 단에서 삭제
    st.session_state.unanswered_df = st.session_state.unanswered_df.drop(drop_indexes)
    #DB 삭제
    hcs.remove_selected_unanswered(drop_indexes)
    #파일 삭제 알림
    delete_row_count = len(drop_indexes)
    st.toast(f"{delete_row_count}건의 파일이 삭제되었습니다.", icon="🗑️")

# Main UI
st.title("무응답 데이터 관리 페이지")

dashboard_placeholder = st.empty()
word_series = analyze_texts(texts, pecab)

unanswered_df = st.session_state.unanswered_df

# [20240912 강태영] 데이터 프레임에 데이터가 있는지 확인
if unanswered_df.empty:
    st.info("저장된 매뉴얼이 없습니다. 매뉴얼을 업로드 해주세요", icon="ℹ️")
else:
    with dashboard_placeholder.container():
        display_dashboard(word_series, unanswered_df)

    # Filters
    col1, col2, col3 = st.columns(3)
    period_filter = col1.date_input("생성날짜", key="period_filter_3", value=None)
    period_filter2 = col2.date_input("처리날짜", key="period_filter_4", value=None)
    category_filter = col3.selectbox("미응답 내용", ["전체"] + list(unanswered_df['미응답 내용'].unique()), key="unanswered_filter_1")

    filtered_df, no_data_warning = filter_data(unanswered_df, period_filter, period_filter2, category_filter)

    if no_data_warning:
        st.warning("선택하신 날짜의 데이터가 존재하지 않습니다.", icon="⚠️")
    else:
        # Pagination controls
        top_menu = st.columns((3, 1, 1))
        batch_size = top_menu[2].selectbox("Page Size", [5, 10, 20, 30, 40, 50], key="batch_size")
        total_pages = (len(filtered_df) // batch_size) + (1 if len(filtered_df) % batch_size else 0)

        # total_pages가 0일 때 페이지네이션 건너뛰기
        if total_pages > 0:
            current_page = top_menu[1].number_input("Page", min_value=1, max_value=total_pages, step=1, key="current_page")
            top_menu[0].markdown(f"Page **{current_page}** of **{total_pages}** ")

            # Add custom CSS to style the data editor
            st.markdown(
                """
                <style>
                .stDataFrame .checkboxColumn {
                    width: 10px !important; 
                }
                </style>
                """,
                unsafe_allow_html=True
            )

    # Display paginated data
            paginated_df = paginate_data(filtered_df, batch_size, current_page)
            if paginated_df is not None:
                edited_df = st.data_editor(
                    paginated_df, 
                    column_config={
                        "선택": st.column_config.CheckboxColumn("", width="tiny"),  # 첫 번째 컬럼 너비 조정
                        "생성날짜": st.column_config.DateColumn(disabled=True),
                        "처리날짜": st.column_config.DateColumn(disabled=True),
                        "미응답 내용": st.column_config.TextColumn(disabled=True),
                        "처리상태": st.column_config.SelectboxColumn(options=["미처리", "처리 완료", "보류"], width="small", required=True)
                    },
                    use_container_width=True,
                    hide_index=True,
                )
                
                # Update session state with selected rows
                selected_rows = edited_df[edited_df['선택'] == True]

                # 버튼을 우측 하단에 배치하기 위한 레이아웃 설정
                button_placeholder = st.empty()  # 버튼 자리를 미리 비워둠

                # 버튼을 우측 하단에 배치
                with button_placeholder.container():
                    col1, col2, col3 = st.columns([5, 2, 1])  # 첫 번째 열은 넓게, 두 번째, 세 번째 열에 버튼 배치
                    with col2:
                        # 데이터 다운로드 버튼
                        file_data = create_download_link(selected_rows, "selected_data.csv")
                        st.download_button(
                            "데이터 다운로드",
                            file_data,
                            "selected_data.csv",
                            mime="text/csv",
                            disabled=selected_rows.empty
                        )
                    with col3:
                        # 삭제 버튼
                        st.button(
                            label="삭제",
                            on_click=removeData,
                            kwargs={"selected_rows": selected_rows},
                            disabled=selected_rows.empty
                        )