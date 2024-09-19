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

# Load unanswered questions and prepare data
unanswered_df = hcs.select_all_unansweredquestions_table()
texts = unanswered_df['QuestionText'].tolist()

unanswered_df.columns = ['생성날짜', '처리날짜', '미응답 내용', '처리상태']
unanswered_df['생성날짜'] = pd.to_datetime(unanswered_df['생성날짜'], errors='coerce')
unanswered_df['처리날짜'] = pd.to_datetime(unanswered_df['처리날짜'], errors='coerce')
unanswered_df.insert(0, "선택", False)

# Analyze and visualize texts
def analyze_texts(texts, pecab, top_n=10):
    font_path = 'Fonts\세스코R_20140905153946.TTF'  # 서버에 맞는 폰트 경로 설정
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
    if period_filter:
        unanswered_df = unanswered_df[unanswered_df['생성날짜'].dt.date == period_filter]
    if period_filter2:
        unanswered_df = unanswered_df[unanswered_df['처리날짜'].dt.date == period_filter2]
    if category_filter != "전체":
        unanswered_df = unanswered_df[unanswered_df['미응답 내용'] == category_filter]
    return unanswered_df

# Pagination
def paginate_data(filtered_df, batch_size, current_page):
    pages = [filtered_df.iloc[i:i + batch_size] for i in range(0, len(filtered_df), batch_size)]
    return pages[current_page - 1] if pages else None

# Download CSV
def create_download_link(df, file_name):
    buffer = io.BytesIO()
    df.to_csv(buffer, index=False, encoding='utf-8-sig')
    buffer.seek(0)
    return st.download_button("매뉴얼 다운로드", buffer.getvalue(), file_name, mime="text/csv", disabled=df.empty)

# Main UI
st.title("무응답 데이터 관리 페이지")

dashboard_placeholder = st.empty()
word_series = analyze_texts(texts, pecab)

with dashboard_placeholder.container():
    display_dashboard(word_series, unanswered_df)

# Date Range Setting
min_date = unanswered_df['생성날짜'].min().date()
max_date = unanswered_df['생성날짜'].max().date()
min_process_date = unanswered_df['처리날짜'].min().date()
max_process_date = unanswered_df['처리날짜'].max().date()

# Filters
col1, col2, col3 = st.columns(3)
period_filter = col1.date_input("생성날짜", key="period_filter_3", min_value=min_date, max_value=max_date)
period_filter2 = col2.date_input("처리날짜", key="period_filter_4", min_value=min_process_date, max_value=max_process_date)
category_filter = col3.selectbox("미응답 내용", ["전체"] + list(unanswered_df['미응답 내용'].unique()), key="unanswered_filter_1")

filtered_df = filter_data(unanswered_df, period_filter, period_filter2, category_filter)

# Pagination controls
top_menu = st.columns((3, 1, 1))
batch_size = top_menu[2].selectbox("Page Size", [5, 10, 20, 30, 40, 50], key="batch_size")
total_pages = (len(filtered_df) // batch_size) + (1 if len(filtered_df) % batch_size else 0)
current_page = top_menu[1].number_input("Page", min_value=1, max_value=total_pages, step=1, key="current_page")
top_menu[0].markdown(f"Page **{current_page}** of **{total_pages}** ")

# Display paginated data
paginated_df = paginate_data(filtered_df, batch_size, current_page)
if paginated_df is not None:
    edited_df = st.data_editor(paginated_df, column_config={
        "선택": st.column_config.CheckboxColumn(),
        "생성날짜": st.column_config.DateColumn(disabled=True),
        "처리날짜": st.column_config.DateColumn(disabled=True),
        "미응답 내용": st.column_config.TextColumn(disabled=True),
        "처리상태": st.column_config.SelectboxColumn(
            options=["미처리", "처리 완료", "보류"], width="small", required=True
        )},
        use_container_width=True
        )
    
    selected_rows = edited_df[edited_df['선택'] == True]
    
    btn_container = st.container()
    with btn_container:
        col1, col2 = st.columns([9, 1])
        with col1:
            create_download_link(selected_rows, "selected_data.csv")
        with col2:
            delete_button = st.button("삭제", disabled=selected_rows.empty)
            if delete_button and not selected_rows.empty:
                for _, row in selected_rows.iterrows():
                    st.write(f"{row['미응답 내용']} 파일을 삭제합니다.")