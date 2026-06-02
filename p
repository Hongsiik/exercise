import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
matplotlib.rcParams['font.family'] = 'Malgun Gothic'

st.title('무신사 랭킹 대시보드')

df = pd.read_csv('musinsa_ranking.csv')

st.subheader('전체 데이터')
st.dataframe(df)

st.subheader('브랜드별 상품 수 Top 10')
brand_count = df['브랜드'].value_counts().head(10)
fig, ax = plt.subplots()
brand_count.plot(kind='bar', ax=ax)
ax.set_xlabel('브랜드')
ax.set_ylabel('상품 수')
plt.xticks(rotation=45)
st.pyplot(fig)

st.subheader('가격대 분포')
fig2, ax2 = plt.subplots()
df['가격'].hist(bins=20, ax=ax2)
ax2.set_xlabel('가격')
ax2.set_ylabel('상품 수')
st.pyplot(fig2)