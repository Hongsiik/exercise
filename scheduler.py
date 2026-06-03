import schedule
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from groq import Groq
import pandas as pd
from datetime import datetime
import os
from dotenv import load_dotenv
from supabase import create_client
load_dotenv()

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

# DB 저장 함수
def save_to_db(df, today):
    # 오늘 데이터 이미 있으면 저장 안 함
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

def crawl_and_analyze():
    print(f'[{datetime.now()}] 크롤링 시작...')

    # 크롤링
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
    driver.get('https://www.musinsa.com/main/musinsa/ranking')
    time.sleep(5)

    data = []
    collected_ids = set()

    for i in range(10):
        items = driver.find_elements(By.CSS_SELECTOR, '.gtm-view-item-list')
        for item in items:
            try:
                item_id = item.get_attribute('data-item-id')
                if item_id in collected_ids:
                    continue
                collected_ids.add(item_id)
                brand = item.find_element(By.CSS_SELECTOR, '.gtm-click-brand p').text
                name = item.find_element(By.CSS_SELECTOR, '.gtm-select-item p').text
                price = item.get_attribute('data-price')
                data.append({'브랜드': brand, '상품명': name, '가격': price})
            except:
                pass
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)

    driver.quit()

    today = datetime.now().strftime('%Y-%m-%d')
    df = pd.DataFrame(data)
    
    # CSV 백업 저장 (날짜별)
    df.to_csv(f'musinsa_{today}.csv', index=False, encoding='utf-8-sig')
    print(f'[{datetime.now()}] {len(df)}개 수집 완료!')

    # ← DB에 바로 저장
    save_to_db(df, today)

    # AI 분석
    top50 = df.head(50).to_string()
    prompt = f"""
당신은 한국 패션 시장 전문 애널리스트입니다. 아래 무신사 랭킹 데이터를 분석해주세요.
반드시 한국어로만 답변하세요. 한자, 일본어, 러시아어 등 다른 언어 문자는 절대 사용하지 마세요.

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