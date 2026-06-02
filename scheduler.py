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

# 대소문자(GROQ_API_KEY)가 금고에 적은 이름과 100% 똑같아야 합니다!
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
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

    # 날짜별 저장
    today = datetime.now().strftime('%Y%m%d')
    df = pd.DataFrame(data)
    df.to_csv(f'musinsa_{today}.csv', index=False, encoding='utf-8-sig')
    print(f'[{datetime.now()}] {len(df)}개 수집 완료!')

    # AI 분석
    client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
    top50 = df.head(50).to_string()
    prompt = f"""
You are a Korean fashion market analyst. Analyze the following Musinsa ranking data and respond ONLY in Korean.

Data:
{top50}

Please analyze:
1. 오늘의 인기 브랜드 특징
2. 가격대별 트렌드
3. 패션 사업자를 위한 비즈니스 제안 3가지
"""
    response = client.chat.completions.create(
        messages=[{'role': 'user', 'content': prompt}],
        model='llama-3.3-70b-versatile',
    )
    result = response.choices[0].message.content

    # 분석 결과 저장
    with open(f'analysis_{today}.txt', 'w', encoding='utf-8') as f:
        f.write(result)
    print(f'[{datetime.now()}] AI 분석 완료!')
    print(result)

# 매일 오전 9시에 실행
schedule.every().day.at('09:00').do(crawl_and_analyze)

print('스케줄러 시작! 매일 오전 9시에 자동 실행됩니다.')

# 테스트용 즉시 실행
crawl_and_analyze()

while True:
    schedule.run_pending()
    time.sleep(60)