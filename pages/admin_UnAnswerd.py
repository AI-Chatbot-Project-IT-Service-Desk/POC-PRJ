import os
import io
import sys
import streamlit as st
import pandas as pd
import pecab
import matplotlib.pyplot as plt
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



# import os
# import io
# import sys
# import streamlit as st
# import json
# import pandas as pd
# import pecab
# import hana_ml
# from hana_ml import ConnectionContext
# from hana_ml.dataframe import create_dataframe_from_pandas
# from gen_ai_hub.proxy.native.openai import embeddings
# from sklearn.feature_extraction.text import TfidfVectorizer
# from collections import Counter
# import matplotlib.pyplot as plt
# import koreanize_matplotlib
# from menu import menu_with_redirect

# sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'server'))

# from server import hana_cloud_service as hcs

# menu_with_redirect()

# unanswered_df = hcs.select_all_unansweredquestions_table()
# texts = unanswered_df['QuestionText'].tolist()

# def analyze_texts_and_visualize(texts, pecab, top_n=10):
#     """
#     텍스트를 분석하고 TF-IDF 기반으로 상위 N개의 단어를 시각화하는 함수.

#     Parameters:
#     texts (list): 분석할 텍스트 리스트
#     pecab (object): 형태소 분석기 객체 (예: PeCab)
#     top_n (int): 상위 단어 N개 (기본값: 10)
#     """
    
#     # 1. 형태소 분석 후 명사만 추출
#     tokenized_texts = [' '.join([word for word, pos in pecab.pos(text) if pos == 'NNG' or pos == 'NNP']) for text in texts]

#     # 2. TF-IDF 계산
#     tfidf = TfidfVectorizer(min_df=1, max_df=0.5)
#     tfidf_matrix = tfidf.fit_transform(tokenized_texts)
#     feature_names = tfidf.get_feature_names_out()

#     # 3. TF-IDF 값이 0 이상인 단어만 추출
#     filtered_words = []
#     for doc_idx in range(tfidf_matrix.shape[0]):
#         for word_idx, score in zip(tfidf_matrix[doc_idx].indices, tfidf_matrix[doc_idx].data):
#             if score > 0:
#                 filtered_words.append(feature_names[word_idx])

#     # 4. 단어 빈도수 계산 및 상위 N개 단어 추출
#     word_count = Counter(filtered_words)
#     most_common_words = word_count.most_common(top_n)

#     # 5. 상위 단어들을 Pandas Series로 변환
#     word_series = pd.Series(dict(most_common_words))

#     # 6. 그래프 시각화
#     fig, ax = plt.subplots(figsize=(10, 6))
#     word_series.plot(kind='bar', color='skyblue', ax=ax)
#     ax.set_title(f'미응답 형태소 분석 Top {top_n} 그래프')
#     ax.set_xlabel('단어')
#     ax.tick_params(axis='x', rotation=0)
#     ax.set_ylabel('빈도 수')

#     # 7. Streamlit으로 그래프 출력
#     st.pyplot(fig)

#     return word_series

# def display_dashboard(word_series, unanswered_df, status_column='처리상태', completed_value='처리 완료'):
#     """
#     Streamlit을 사용하여 3가지 주요 지표를 대시보드 형태로 출력하는 함수.

#     Parameters:
#     word_series (pd.Series): 단어 빈도 시리즈
#     unanswered_df (pd.DataFrame): 데이터프레임 (상태 정보 포함)
#     status_column (str): '처리 완료' 상태를 담고 있는 열 이름 (기본값: '처리 상태')
#     completed_value (str): '처리 완료'로 표시된 상태 값 (기본값: '처리 완료')
#     """
    
#     # 1. 가장 많은 빈도수를 차지한 단어와 그 빈도수
#     top_word = word_series.idxmax()
#     top_word_count = word_series.max()

#     # 2. 미응답 데이터 수
#     missing_data_count = unanswered_df.shape[0]  # 데이터프레임의 총 행 수 (미응답으로 가정)

#     # 3. '처리 완료' 상태 비율 계산
#     completed_status_count = unanswered_df[unanswered_df[status_column] == completed_value].shape[0]
#     total_count = unanswered_df.shape[0]
#     completed_percentage = (completed_status_count / total_count) * 100

#     # 4. Streamlit 컬럼으로 대시보드 출력
#     col1, col2, col3 = st.columns(3)

#     # col1: 가장 많은 빈도수를 차지한 단어
#     col1.metric("Most Common Word", f"{top_word}", f"{top_word_count} occurrences")

#     # col2: 총 미응답 데이터 수
#     col2.metric("Missing Data Count", str(missing_data_count))

#     # col3: '처리 완료' 비율
#     col3.metric("Completion Rate", f"{completed_percentage:.2f}%", "Percentage of completed status")

# unanswered_df.columns = ['생성날짜', '처리날짜', '미응답 내용', '처리상태']
# unanswered_df['생성날짜'] = pd.to_datetime(unanswered_df['생성날짜'], errors='coerce')
# unanswered_df['처리날짜'] = pd.to_datetime(unanswered_df['처리날짜'], errors='coerce')
# unanswered_df.insert(0, "선택", False)

# pecab = pecab.PeCab()
# # analyze_texts_and_visualize(texts, pecab, top_n=10)
# st.title("무응답 데이터 관리 페이지")

# dashboard_placeholder = st.empty()

# # 2. 단어 분석 결과 출력
# word_series = analyze_texts_and_visualize(texts, pecab)

# # 3. 나중에 대시보드 출력 (위에서 만든 자리에서)
# with dashboard_placeholder.container():
#     display_dashboard(word_series, unanswered_df)

# col1, col2, col3 = st.columns(3)

# with col1:
#     period_filter = st.date_input("생성날짜", key="period_filter_3", value=None)  # 고유한 키 사용
# with col2:
#     period_filter2 = st.date_input("처리날짜", key="period_filter_4", value=None)  # 고유한 키 사용
# with col3:
#     category_filter = st.selectbox("미응답 내용", options=["전체"] + list(unanswered_df['미응답 내용'].unique()), key="unanswered_filter_1")  # 고유한 키 사용

# # 필터 조건 확인
# has_filters = any([
#     period_filter is not None,
#     category_filter != "전체"
# ])

# has_filters2 = any([
#     period_filter2 is not None,
#     category_filter != "전체"
# ])

# # 유효성 검사 및 필터 적용
# invalid_input = False
# if period_filter:
#     valid_dates = unanswered_df['생성날짜'].dt.date.tolist()
#     if period_filter not in valid_dates:
#         invalid_input = True

# if period_filter2:
#     valid_dates = unanswered_df['처리날짜'].dt.date.tolist()
#     if period_filter2 not in valid_dates:
#         invalid_input = True

# if category_filter != "전체":
#     valid_categories = unanswered_df['미응답 내용'].unique().tolist()
#     if category_filter not in valid_categories:
#         invalid_input = True

# if invalid_input and has_filters and has_filters2:
#     st.error("선택하신 날짜의 문서가 존재하지 않습니다.")

# else:
#     # 필터 적용
#     filtered_df = unanswered_df.copy()  # 필터링 전 전체 데이터를 기본으로 표시

#     if period_filter:
#         filtered_df = filtered_df[filtered_df['생성날짜'].dt.date == period_filter]
#     if period_filter2:
#         filtered_df = filtered_df[filtered_df['처리날짜'].dt.date == period_filter2]
#     if category_filter != "전체":
#         filtered_df = filtered_df[filtered_df['미응답 내용'] == category_filter]
    
#     # 페이지네이션을 위한 설정
#     pagination = st.container()

#     # 버튼 클릭 시 페이지 업데이트
#     if 'current_page' not in st.session_state:
#         st.session_state.current_page = 1
    
#     top_menu = st.columns((3, 1, 1))
    
#     with top_menu[2]:
#         batch_size = st.selectbox("Page Size", options=[5, 10, 20, 30, 40, 50], key="batch_size")
#     with top_menu[1]:
#         total_pages = ((len(filtered_df) // batch_size) + (1 if len(filtered_df) % batch_size > 0 else 0))
#         current_page = st.number_input("Page", min_value=1, max_value=total_pages, step=1, key="current_page")
#     with top_menu[0]:
#         st.markdown(f"Page **{st.session_state.current_page}** of **{total_pages}** ")

#     # 데이터 페이지 나누기
#     def split_frame(input_df, rows):
#         return [input_df.iloc[i:i + rows] for i in range(0, len(input_df), rows)]
    
#     pages = split_frame(filtered_df, batch_size)
#     if total_pages > 0:
#         # st.data_editor를 사용하여 체크박스를 포함한 데이터 표시
#         edited_df = st.data_editor(
#             pages[st.session_state.current_page - 1],
#             column_config={
#                 "선택": st.column_config.CheckboxColumn(),  # 체크박스는 수정 가능
#                 "생성날짜": st.column_config.DateColumn(disabled=True),  # 수정 불가
#                 "처리날짜": st.column_config.DateColumn(disabled=True),  # 수정 불가
#                 "미응답 내용": st.column_config.TextColumn(disabled=True),
#                 '처리상태': st.column_config.SelectboxColumn(disabled=False,
#                                                             width="small",
#                                                             options=[
#                                                                 "미처리",
#                                                                 "처리 완료",
#                                                                 "보류"
#                                                             ],
#                                                             default="미처리",
#                                                             required=True)
#                 },
#             use_container_width=True,
#             )
        
#         # 체크박스를 선택한 항목만 다운로드 및 삭제 기능
#         selected_rows = edited_df[edited_df['선택'] == True]
        
#         # 버튼을 배치할 빈 컨테이너
#         btn_container = st.container()
#         with btn_container:
#             # 빈 공간을 만들기 위한 두 개의 빈 열
#             top_menu_empty = st.columns((3, 3, 2, 1))

#             # 다운로드 링크 생성 함수
#             with top_menu_empty[2]:
#                 def create_download_link(df, file_name):
#                     buffer = io.BytesIO()
#                     df.to_csv(buffer, index=False, encoding='utf-8-sig')
#                     buffer.seek(0)
#                     return st.download_button(
#                         label="매뉴얼 다운로드",
#                         data=buffer.getvalue(),
#                         file_name=file_name,
#                         mime="text/csv",
#                         disabled=df.empty  # 선택된 항목이 없을 경우 버튼 비활성화
#                     )
#                 # '매뉴얼 다운로드' 버튼을 항상 표시
#                 create_download_link(selected_rows, "selected_data.csv")

#             # 삭제 버튼
#             with top_menu_empty[3]:
#                 delete_button = st.button(
#                     label="삭제",
#                     disabled=selected_rows.empty  # 선택된 항목이 없으면 비활성화
#                 )

#                 if delete_button and not selected_rows.empty:
#                     # 선택된 파일 삭제 처리 로직 (예: DB에서 삭제)
#                     for index, row in selected_rows.iterrows():
#                         # 여기에 실제 삭제 로직 구현 (DB에서 삭제 등)
#                         st.write(f"{row['미응답 내용']} 파일을 삭제합니다.")
                    
#                     # 삭제가 완료되면 페이지를 다시 로드하여 데이터 갱신
#                     st.session_state.reload = True
#     else:
#         st.warning("해당 조건에 맞는 데이터가 없습니다.")




# # df2 = st.data_editor(df.reset_index(drop=True), hide_index=True)
# def paginate_data(df, items_per_page):
#     # 총 페이지 수 계산
#     total_pages = len(df) // items_per_page + (1 if len(df) % items_per_page > 0 else 0)

#     # 현재 페이지 선택
#     page = st.number_input("페이지 번호", min_value=1, max_value=total_pages, value=1)
    
#     # 해당 페이지 데이터 추출
#     start_idx = (page - 1) * items_per_page
#     end_idx = start_idx + items_per_page
#     current_data = df.iloc[start_idx:end_idx]
    
#     # 페이지네이션 정보 반환
#     return current_data, page, total_pages

# # 데이터 페이지네이션 적용 (10개씩 구분)
# items_per_page = 10
# current_data, page, total_pages = paginate_data(df, items_per_page)

# # 현재 페이지의 데이터 출력
# st.data_editor(current_data.reset_index(drop=True),
#                         hide_index=True,
#                         column_config={ 'Select': st.column_config.CheckboxColumn("Your favorite?", default=False),
#                                         'QuestionID': st.column_config.Column(disabled=True),
#                                         'QuestionText': st.column_config.Column(disabled=True),
#                                         'Status': st.column_config.SelectboxColumn(disabled=False,
#                                                                                     width="small",
#                                                                                     options=[
#                                                                                         "미처리",
#                                                                                         "처리 완료",
#                                                                                         "보류"
#                                                                                     ],
#                                                                                     default="미처리",
#                                                                                     required=True),
#                                         'StatusUpdateDate': st.column_config.Column(disabled=True),
#                                         'DownloadDate': st.column_config.Column(disabled=True),
#                                         'CreateDate': st.column_config.Column(disabled=True)
#                                     },
#                         # num_rows="dynamic"  # 행 추가 기능 비활성화
#                         )

# # 페이지네이션 정보 표시
# st.write(f"Page {page} of {total_pages}")