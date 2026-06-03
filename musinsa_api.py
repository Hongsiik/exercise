import requests
import json

def crawl_musinsa():
    data = []
    page = 1
    start_rank = 1
    
    while True:
        url = f"https://client.musinsa.com/api/home/web/v5/pans/ranking/sections/200?storeCode=musinsa&gf=A&ageBand=AGE_BAND_ALL&period=REALTIME&eventPeriod=BASIC_REALTIME&categoryCode=000&contentsId=&variantValue=&page={page}&startRank={start_rank}&offset={start_rank-1}"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers)
        result = response.json()
        
        # 상품 파싱
        for section in result['data']['modules']:
            for item in section.get('items', []):
                if item.get('type') == 'PRODUCT_COLUMN':
                    try:
                        data.append({
                            '브랜드': item['info']['brandName'],
                            '상품명': item['info']['productName'],
                            '가격': item['info']['finalPrice'],
                            '순위': item['image']['rank']
                        })
                    except:
                        pass
        
        # 다음 페이지 있는지 확인
        next_url = result.get('link', {}).get('next')
        if not next_url:
                break
        page += 1
        start_rank += 100
        
        if page > 10:  # 최대 1000개
            break
    
    print(f'{len(data)}개 수집 완료!')
    return data

if __name__ == '__main__':
    data = crawl_musinsa()
    print(data[:3])  # 처음 3개만 출력