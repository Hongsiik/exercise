import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
from groq import Groq
import os
import sqlite3
try:
    from dotenv import load_dotenv
    load_dotenv()
except:
    pass
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

matplotlib.rcParams['font.family'] = 'Malgun Gothic'

st.title('무신사 랭킹 대시보드')

df = pd.read_csv('musinsa_ranking.csv')
df['수집날짜'] = '2026-06-02'  # 날짜 컬럼 수동 추가
dates = ['전체', '2026-06-02']

dates = ['전체'] + df['수집날짜'].unique().tolist()


# 가격대 컬럼 추가
bins = [0, 30000, 50000, 80000, 120000, df['가격'].max()]
labels = ['0~3만원', '3~5만원', '5~8만원', '8~12만원', '12만원 이상']
df['가격대'] = pd.cut(df['가격'], bins=bins, labels=labels)

# ─────────────────────────────
# 1. 필터 기능
# ─────────────────────────────
st.sidebar.title('필터')
selected_date = st.sidebar.selectbox('날짜 선택', dates)



# 가격 슬라이더
min_price, max_price = st.sidebar.slider(
    '가격 범위',
    int(df['가격'].min()),
    int(df['가격'].max()),
    (int(df['가격'].min()), int(df['가격'].max()))
)

# 브랜드 드롭다운
brands = ['전체'] + sorted(df['브랜드'].unique().tolist())
selected_brand = st.sidebar.selectbox('브랜드 선택', brands)

# 필터 적용
filtered_df = df[(df['가격'] >= min_price) & (df['가격'] <= max_price)]
if selected_brand != '전체':
    filtered_df = filtered_df[filtered_df['브랜드'] == selected_brand]

if selected_date != '전체':
    filtered_df = filtered_df[filtered_df['수집날짜'] == selected_date]

# ─────────────────────────────
# 2. 전체 데이터
# ─────────────────────────────
st.subheader(f'전체 데이터 ({len(filtered_df)}개)')
st.dataframe(filtered_df)

# ─────────────────────────────
# 3. 브랜드별 상품 수 Top10
# ─────────────────────────────
st.subheader('브랜드별 상품 수 Top 10')
brand_count = filtered_df['브랜드'].value_counts().head(10)
fig, ax = plt.subplots(figsize=(10, 5))
brand_count.plot(kind='bar', ax=ax)
ax.set_xlabel('브랜드')
ax.set_ylabel('상품 수')
plt.xticks(rotation=45)
plt.tight_layout()
st.pyplot(fig)

# ─────────────────────────────
# 4. 가격대 분포
# ─────────────────────────────
st.subheader('가격대 분포')
fig2, ax2 = plt.subplots(figsize=(10, 5))
price_count = filtered_df['가격대'].value_counts().sort_index()
ax2.plot(price_count.index, price_count.values, marker='o', linewidth=2)
ax2.set_xlabel('가격대')
ax2.set_ylabel('상품 수')
plt.tight_layout()
st.pyplot(fig2)


# ─────────────────────────────
# 5. AI 분석 버튼
# ─────────────────────────────
st.subheader('AI 분석')
if st.button('AI 분석 실행'):
    with st.spinner('분석 중...'):
        client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
        top50 = filtered_df.head(50).to_string()
        prompt = f"""
You are a Korean fashion market analyst. Analyze the following Musinsa ranking data and respond ONLY in Korean. Do not use any other language including English, Japanese, or Chinese.

Data:
{top50}

Please analyze:
1. 인기 브랜드 특징
2. 가격대별 트렌드  
3. 패션 사업자를 위한 비즈니스 제안 3가지

IMPORTANT: Respond in Korean only. Never use English, Japanese, or Chinese words.
"""
        

        
        response = client.chat.completions.create(
            messages=[{'role': 'user', 'content': prompt}],
            model='llama-3.3-70b-versatile',
        )
        st.write(response.choices[0].message.content)

