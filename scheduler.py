import schedule
import time
from groq import Groq
import pandas as pd
from datetime import datetime
import os
from dotenv import load_dotenv
from supabase import create_client
from musinsa_api import crawl_musinsa, crawl_by_category

load_dotenv()

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

# 전체 랭킹 저장
def save_to_db(df, today):
    existing = supabase.table('ranking').select('id').eq('수집날짜', today).execute()
    if len(existing.data) > 0:
        print(f'오늘({today}) ranking 데이터 이미 있음. 저장 건너뜀.')
    else:
        records = df.to_dict('records')
        for record in records:
            record['수집날짜'] = today
            record['가격'] = int(record['가격']) if record['가격'] else 0
        supabase.table('ranking').insert(records).execute()
        print(f'{len(df)}개 ranking 저장 완료!')

# 카테고리별 랭킹 저장
def save_category_to_db(df, today):
    existing = supabase.table('ranking_by_category').select('id').eq('수집날짜', today).execute()
    if len(existing.data) > 0:
        print(f'오늘({today}) ranking_by_category 데이터 이미 있음. 저장 건너뜀.')
    else:
        records = df.to_dict('records')
        for record in records:
            record['수집날짜'] = today
            record['가격'] = int(record['가격']) if record['가격'] else 0
        supabase.table('ranking_by_category').insert(records).execute()
        print(f'{len(df)}개 ranking_by_category 저장 완료!')

def crawl_and_analyze():
    print(f'[{datetime.now()}] 크롤링 시작...')
    today = datetime.now().strftime('%Y-%m-%d')

    # 전체 랭킹 수집
    data = crawl_musinsa()
    df = pd.DataFrame(data)
    df.to_csv(f'musinsa_{today}.csv', index=False, encoding='utf-8-sig')
    save_to_db(df, today)

    # 카테고리별 랭킹 수집
    category_data = crawl_by_category()
    df_category = pd.DataFrame(category_data)
    df_category.to_csv(f'musinsa_category_{today}.csv', index=False, encoding='utf-8-sig')
    save_category_to_db(df_category, today)

    # AI 분석
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
    result = response.choices[0].message.content
    with open(f'analysis_{today}.txt', 'w', encoding='utf-8') as f:
        f.write(result)
    print(f'[{datetime.now()}] AI 분석 완료!')
    print(result)

schedule.every().day.at('09:00').do(crawl_and_analyze)
print('스케줄러 시작! 매일 오전 9시에 자동 실행됩니다.')

crawl_and_analyze()

while True:
    schedule.run_pending()
    time.sleep(60)