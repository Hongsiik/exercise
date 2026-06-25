import requests

def crawl_musinsa():
    """전체 랭킹 수집 (ranking 테이블용)"""
    data = []
    page = 1
    start_rank = 1

    while True:
        url = f"https://client.musinsa.com/api/home/web/v5/pans/ranking/sections/200?storeCode=musinsa&gf=A&ageBand=AGE_BAND_ALL&period=REALTIME&eventPeriod=BASIC_REALTIME&categoryCode=000&contentsId=&variantValue=&page={page}&startRank={start_rank}&offset={start_rank-1}"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

        response = requests.get(url, headers=headers)
        result = response.json()

        for section in result['data']['modules']:
            for item in section.get('items', []):
                if item.get('type') == 'PRODUCT_COLUMN':
                    try:
                        data.append({
                            '브랜드': item['info']['brandName'],
                            '상품명': item['info']['productName'],
                            '가격': item['info']['finalPrice'],
                            '순위': item['image']['rank'],
                        })
                    except:
                        pass

        next_url = result.get('link', {}).get('next')
        if not next_url:
            break
        page += 1
        start_rank += 100
        if page > 10:
            break

    print(f'전체 랭킹 {len(data)}개 수집 완료!')
    return data


def crawl_by_category():
    """카테고리별 수집 - 스포츠 브랜드 필터링"""
    
    CATEGORIES = {
        '스포츠/레저': '017000',
        '신발': '103000',
        '상의': '001000',
        '바지': '003000',
    }

    all_data = []
    for category_name, category_code in CATEGORIES.items():
        data = []
        page = 1
        start_rank = 1

        while True:
            url = f"https://client.musinsa.com/api/home/web/v5/pans/ranking/sections/200?storeCode=musinsa&gf=A&ageBand=AGE_BAND_ALL&period=REALTIME&eventPeriod=BASIC_REALTIME&categoryCode={category_code}&contentsId=&variantValue=&page={page}&startRank={start_rank}&offset={start_rank-1}"
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

            response = requests.get(url, headers=headers)
            result = response.json()

            for section in result['data']['modules']:
                for item in section.get('items', []):
                    if item.get('type') == 'PRODUCT_COLUMN':
                        try:
                            data.append({
                                '브랜드': item['info']['brandName'],
                                '상품명': item['info']['productName'],
                                '가격': item['info']['finalPrice'],
                                '순위': item['image']['rank'],
                                '카테고리': category_name,
                                # 아래 두 줄 추가
                                '리뷰수': item['onClick']['eventLog']['amplitude']['payload'].get('reviewCount', 0),
                                '리뷰점수': item['onClick']['eventLog']['amplitude']['payload'].get('reviewScore', 0),
                            })
                        except:
                            pass

            next_url = result.get('link', {}).get('next')
            if not next_url:
                break
            page += 1
            start_rank += 100
            if page > 10:
                break

        print(f'[{category_name}] {len(data)}개 수집 완료!')
        all_data.extend(data)

    print(f'카테고리별 총 {len(all_data)}개 수집 완료!')
    return all_data