import streamlit as st
import pandas as pd

# 샘플 데이터 생성
data = {
    '선택': [False, False, False, False, False],
    '이름': ['진욱', '현수', '민지', '수현', '서준'],
    '나이': [28, 22, 24, 30, 26],
    '직업': ['개발자', '디자이너', '기획자', '엔지니어', '마케터']
}

df = pd.DataFrame(data)

# 전체 선택 상태를 관리할 변수
select_all = st.checkbox('전체 선택')

# 전체 선택 상태에 따라 '선택' 열의 값 업데이트
if select_all:
    df['선택'] = True
else:
    df['선택'] = False

# 데이터 에디터로 데이터 표시
edited_df = st.data_editor(
    df,
    column_config={
        '선택': st.column_config.CheckboxColumn("선택", width="tiny"),
        '이름': st.column_config.TextColumn("이름"),
        '나이': st.column_config.NumberColumn("나이"),
        '직업': st.column_config.TextColumn("직업")
    },
    hide_index=True
)

# 총 데이터 개수 출력
st.write(f"총 {len(edited_df)}개의 데이터가 있습니다.")