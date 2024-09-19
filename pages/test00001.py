import streamlit as st
import pandas as pd

# 샘플 데이터 생성
data = {
    '선택': [False, False, False],  # 선택 열 추가
    '이름': ['진욱', '현수', '민지'],
    '나이': [28, 22, 24],
    '직업': ['개발자', '디자이너', '기획자']
}

df = pd.DataFrame(data)

# DataFrame의 선택 열을 수정 가능하게, 나머지 열은 수정 불가능하게 설정
edited_df = st.data_editor(
    df,
    column_config={
        '선택': st.column_config.CheckboxColumn(
            "선택", help="항목을 선택하세요."
        ),
        '이름': st.column_config.TextColumn(
            "이름", help="이름 열", disabled=True  # 수정 불가능
        ),
        '나이': st.column_config.NumberColumn(
            "나이", help="나이 열", disabled=True  # 수정 불가능
        ),
        '직업': st.column_config.TextColumn(
            "직업", help="직업 열", disabled=True  # 수정 불가능
        )
    },
    hide_index=True,  # 인덱스 열 숨기기
    num_rows="fixed"  # 행 추가 기능 비활성화
)

# 선택된 항목 출력 (선택한 행의 데이터를 보여줌)
st.write("선택된 항목:", edited_df[edited_df['선택']])
