
from groq import Groq
import pandas as pd

client = Groq(api_key='hi')

df = pd.read_csv('musinsa_ranking.csv')
top50 = df.head(50).to_string()

prompt = f"""
다음은 무신사 실시간 랭킹 상위 50개 상품 데이터야.
{top50}

이 데이터를 분석해서 알려줘.
1. 현재 무신사에서 인기있는 브랜드 특징
2. 가격대별 트렌드
3. 패션 브랜드 사업자를 위한 비즈니스 제안 3가지
한국어로 답해줘.
"""

chat_completion = client.chat.completions.create(
    messages=[
        {'role': 'user', 'content': prompt}
    ],
    model='llama-3.3-70b-versatile',
)

print(chat_completion.choices[0].message.content)