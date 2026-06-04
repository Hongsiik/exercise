import requests
import json

url = "https://client.musinsa.com/api/home/web/v5/pans/ranking/sections/200?storeCode=musinsa&gf=A&ageBand=AGE_BAND_ALL&period=REALTIME&eventPeriod=BASIC_REALTIME&categoryCode=000&contentsId=&variantValue=&page=1&startRank=1&offset=0"
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

response = requests.get(url, headers=headers)
result = response.json()

for section in result['data']['modules']:
    items = section.get('items', [])
    if items:
        for item in items:
            if item.get('type') == 'PRODUCT_COLUMN':
                # impressionEventLog만 출력
                imp = item.get('impressionEventLog', {})
                print(json.dumps(imp, ensure_ascii=False, indent=2)[:2000])
                break
        break