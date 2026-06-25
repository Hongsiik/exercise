import requests
import json

base_url = "https://api.musinsa.com/api2/dp/v1/ranking-archive/goods"
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

# 테스트할 파라미터 조합들
test_params = [
    {'yearMonth': '202605', 'gf': 'A', 'category': '017', 'page': 2},
    {'yearMonth': '202605', 'gf': 'A', 'category': '017', 'size': 100},
    {'yearMonth': '202605', 'gf': 'A', 'category': '017', 'startRank': 31},
    {'yearMonth': '202605', 'gf': 'A', 'category': '017', 'offset': 30},
]

for i, params in enumerate(test_params):
    response = requests.get(base_url, params=params, headers=headers)
    result = response.json()
    items = result.get('data', {}).get('list', [])
    
    print(f"\n[테스트 {i+1}] params: {params}")
    print(f"  → 받은 개수: {len(items)}")
    if items:
        print(f"  → 첫 상품 순위: {items[0].get('rank')}")
        print(f"  → 마지막 상품 순위: {items[-1].get('rank')}")