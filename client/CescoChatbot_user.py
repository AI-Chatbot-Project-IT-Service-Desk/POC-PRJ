import streamlit as st
import pandas as pd

# 테이블을 위한 샘플 데이터
sample_data = {
    '생성 날짜': ['2024.08.01'] * 10,
    '카테고리': ['카테고리입니다.'] * 10,
    '키워드': ['키워드입니다.'] * 10,
    '문제': [
        '문제 확인필요.',
        '데이터 오류.',
        '서버 연결 실패.',
        '사용자 입력 오류.',
        '인증 오류.',
        '네트워크 문제.',
        'API 호출 오류.',
        '페이지 로드 실패.',
        '시간 초과.',
        '메모리 부족.'
    ],
    '링크': ['http://example.com'] * 10,  # 샘플 링크 추가
}

# 사전을 DataFrame으로 변환
df = pd.DataFrame(sample_data)

# 사이드바 배경색 및 버튼 스타일 변경을 위한 커스텀 CSS 추가
st.markdown(
    """
    <style>
    [data-testid="stSidebar"] {
        background-color:#E0F7FA; /* 연한 파란색 */
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.title("Manual List 📑")
st.markdown("<hr style='border:1.5px solid #E0F7FA'>", unsafe_allow_html=True)

df['생성 날짜'] = pd.to_datetime(df['생성 날짜'], format='%Y.%m.%d')

# 헤더 행에 대한 필터
st.markdown("<div style='margin-bottom: 30px;'></div>", unsafe_allow_html=True)  # 추가된 간격
col4, col5, col6, col7, col8 = st.columns(5)

with col4:
    period_filter = st.date_input("기간", value=None)  # 기본값을 None으로 설정
with col5:
    category_filter = st.selectbox("카테고리", options=["전체"] + list(df['카테고리'].unique()))
with col6:
    keyword_filter = st.selectbox("키워드", options=["전체"] + list(df['키워드'].unique()))
with col7:
    # 문제 검색 텍스트 입력
    issue_filter = st.text_input("문제 검색", value="", placeholder="문제를 검색하세요")
with col8:
    st.write("상세보기")

# 필터 적용
filtered_df = df[
    ((df['생성 날짜'] == pd.to_datetime(period_filter)) if period_filter else True) &
    ((df['카테고리'] == category_filter) if category_filter != "전체" else True) &
    ((df['키워드'] == keyword_filter) if keyword_filter != "전체" else True) &
    (df['문제'].str.contains(issue_filter, case=False, na=False) if issue_filter else True)
]

# 페이지네이션 설정
items_per_page = 10
total_items = len(filtered_df)
total_pages = (total_items // items_per_page) + (1 if total_items % items_per_page != 0 else 0)

# 페이지가 있을 때만 페이지네이션 슬라이더 추가
if total_pages > 0:
    page = st.slider("Select page", 1, total_pages, 1)
else:
    page = 1  # 항목이 없을 경우 기본 페이지

start_idx = (page - 1) * items_per_page
end_idx = start_idx + items_per_page
paginated_df = filtered_df.iloc[start_idx:end_idx]

# "상세보기" 버튼이 있는 페이지네이션 DataFrame 표시
st.write("<style> .css-1cpxqw2 {margin-top: -30px;} </style>", unsafe_allow_html=True)
st.table(paginated_df[['생성 날짜', '카테고리', '키워드', '문제']])
for i, row in paginated_df.iterrows():
    if st.button("상세보기", key=f"details_{i}"):
        st.session_state.current_url = row['링크']

# 세션 상태에 따라 링크 표시
if 'current_url' in st.session_state:
    st.markdown(f"[링크 열기]({st.session_state.current_url})")
    del st.session_state.current_url

# 선택된 행의 세부 정보 표시
selected_rows = paginated_df

if not selected_rows.empty:
    st.write("선택된 항목 세부 정보:")
    for _, row in selected_rows.iterrows():
        st.write(f"**행 {row.name}:**")
        st.write(row)
        st.markdown(f"[링크 열기]({row['링크']})")  # 링크 표시

# 푸터
st.markdown("<h5 style='text-align: center;'>페이지 이동</h5>", unsafe_allow_html=True)
page_numbers = list(range(1, total_pages + 1))

# 페이지가 있을 때만 열 생성
if page_numbers:
    cols = st.columns(len(page_numbers))
    for i, page_number in enumerate(page_numbers):
        if cols[i].button(str(page_number), key=f"page_{page_number}"):
            page = page_number
