import requests
import json

url = "https://client.musinsa.com/api/home/web/v5/pans/ranking/sections/200?storeCode=musinsa&gf=A&ageBand=AGE_BAND_ALL&period=REALTIME&eventPeriod=BASIC_REALTIME&categoryCode=000&contentsId=&variantValue=&page=1&startRank=1&offset=0"

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

response = requests.get(url, headers=headers)
result = response.json()

# 최상위 키 확인
print("최상위 키:", result.keys())

# data 안에 뭐가 있는지
print("data 안 키:", result['data'].keys())
