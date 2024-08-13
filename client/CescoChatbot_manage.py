import streamlit as st
import pandas as pd

# Sample data for the table
sample_data = {
    '기간': ['2024.08.01'] * 10,
    '카테고리': ['카테고리입니다.'] * 10,
    '키워드': ['키워드입니다.'] * 10,
    '문제': ['문제 확인필요.'] * 10,
    '링크': ['http://example.com'] * 10,  # Add sample links
}

# Convert the dictionary to a DataFrame
sample_df = pd.DataFrame(sample_data)

# Add custom CSS to change the sidebar background color
st.markdown(
    """
    <style>
    [data-testid="stSidebar"] {
        background-color:#E0F7FA; /* Light blue */
    }
    .stButton button {
        background-color: #0085CA;
        color: white;
    }
    </style>

    }
    </style>
    """,
    unsafe_allow_html=True
)

# Sidebar layout
st.sidebar.title("🐛CESCO BOT🐛")
st.sidebar.button("Cesco Bot Home")
st.sidebar.button("Manual List")
st.sidebar.button("미응답 대시보드")

if st.sidebar.button("Setting"):
    st.sidebar.subheader("설정 메뉴")
    setting_option = st.sidebar.selectbox("", ("원본 데이터 관리", "QnA 데이터 관리", "미응답 데이터 관리"))

# Main content
st.title("")

# Action buttons aligned horizontally to the right
col1, col2, col3, col4 = st.columns([5, 2, 2, 1])  # Adjust column width to push buttons to the right
with col1:
    st.write("")  # Empty column to push the buttons to the right
with col2:
    upload_button = st.button("데이터 업로드", key="upload")
    print("태영", upload_button)
    st.markdown('<div id="upload_button"></div>', unsafe_allow_html=True)
with col3:
    download_button = st.button("양식 다운로드", key="download")
    st.markdown('<div id="download_button"></div>', unsafe_allow_html=True)
with col4:
    delete_button = st.button("삭제", key="delete")
    st.markdown('<div id="delete_button"></div>', unsafe_allow_html=True)

# File upload
uploaded_file = st.file_uploader("pdf 파일 업로드", type="pdf")

if uploaded_file:
    # Read the uploaded XLSX file
    df = pd.read_fwf(uploaded_file)
else:
    df = sample_df

df['기간'] = pd.to_datetime(df['기간'], format='%Y.%m.%d')

# Filters for the header row
col4, col5, col6, col7, col8 = st.columns(5)

with col4:
    period_filter = st.date_input("기간")
with col5:
    category_filter = st.selectbox("카테고리", options=["전체"] + list(df['카테고리'].unique()))
with col6:
    keyword_filter = st.selectbox("키워드", options=["전체"] + list(df['키워드'].unique()))
with col7:
    issue_filter = st.selectbox("문제", options=["전체"] + list(df['문제'].unique()))
with col8:
    st.write("상세보기")

# Apply filters
filtered_df = df[
    ((df['기간'] == pd.to_datetime(period_filter)) if period_filter else True) &
    ((df['카테고리'] == category_filter) if category_filter != "전체" else True) &
    ((df['키워드'] == keyword_filter) if keyword_filter != "전체" else True) &
    ((df['문제'] == issue_filter) if issue_filter != "전체" else True)
]

# Add a column for checkboxes
filtered_df['선택'] = False

# All select checkbox
select_all = st.checkbox("전체 선택", key="select_all")

# Display the filtered DataFrame with checkboxes and "상세보기" button
for i, row in filtered_df.iterrows():
    cols = st.columns(len(filtered_df.columns))  # Create columns for each item in the row (excluding the checkbox)
    selected = cols[0].checkbox(f"{i}", value=select_all or row['선택'], key=f"checkbox_{i}")
    filtered_df.at[i, '선택'] = selected  # Update the DataFrame with the checkbox value
    for col, value in zip(cols[1:], row[:-2]):  # Exclude the last two columns (URL and checkbox)
        col.write(value)
    if cols[-1].button("상세보기", key=f"details_{i}"):
       st.session_state.current_url = row['상세보기']

# Display the link based on session state
if 'current_url' in st.session_state:
    st.markdown(f"[링크 열기]({st.session_state.current_url})")
    del st.session_state.current_url

# Display selected rows' details
selected_rows = filtered_df[filtered_df['선택']]
if not selected_rows.empty:
    st.write("선택된 항목 세부 정보:")
    for _, row in selected_rows.iterrows():
        st.write(f"**행 {row.name}:**")
        st.write(row)
        st.markdown(f"[링크 열기]({row['링크']})")  # Display link

# Pagination (dummy example for visual representation)
st.write("Page navigation")
page = st.slider("Select page", 1, 16, 1)
st.write(f"Current page: {page}")

if not selected_rows.empty:
    st.write("선택된 항목 세부 정보:")
    for _, row in selected_rows.iterrows():
        st.write(f"**행 {row.name}:**")
