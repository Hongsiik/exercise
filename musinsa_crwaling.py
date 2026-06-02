from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
import time
import pandas as pd

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
driver.get('https://www.musinsa.com/main/musinsa/ranking')
time.sleep(5)

data = []
collected_ids = set()

for i in range(20):
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
    print(f'{i+1}번 스크롤 - 현재 {len(data)}개 수집')

df = pd.DataFrame(data)
df.to_csv('musinsa_ranking.csv', index=False, encoding='utf-8-sig')
print(f'총 {len(df)}개 수집 완료!')