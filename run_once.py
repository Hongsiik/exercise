from musinsa_api import crawl_musinsa
from supabase import create_client
from groq import Groq
from datetime import datetime
import pandas as pd
import os
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

def save_to_db(df, today):
    existing = supabase.table('ranking').select('id').eq('수집날짜', today).execute()
    if len(existing.data) > 0:
        print(f'오늘({today}) 데이터 이미 있음. 저장 건너뜀.')
    else:
        records = df.to_dict('records')
        for record in records:
            record['수집날짜'] = today
            record['가격'] = int(record['가격']) if record['가격'] else 0
        supabase.table('ranking').insert(records).execute()
        print(f'{len(df)}개 데이터 Supabase 저장 완료!')

print(f'[{datetime.now()}] 크롤링 시작...')
data = crawl_musinsa()
today = datetime.now().strftime('%Y-%m-%d')
df = pd.DataFrame(data)

save_to_db(df, today)

top50 = df.head(50).to_string()
prompt = f"""
당신은 한국 패션 시장 전문 애널리스트입니다. 아래 무신사 랭킹 데이터를 분석해주세요.
반드시 한국어로만 답변하세요.

데이터:
{top50}

다음 항목을 분석해주세요:
1. 오늘의 인기 브랜드 특징
2. 가격대별 트렌드
3. 패션 사업자를 위한 비즈니스 제안 3가지
"""

response = client.chat.completions.create(
    messages=[{'role': 'user', 'content': prompt}],
    model='llama-3.3-70b-versatile',
)
print(response.choices[0].message.content)
print(f'[{datetime.now()}] 완료!')