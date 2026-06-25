import requests
import json
import os
import statistics
from collections import defaultdict
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

TOKEN = "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjo3NDAxMzAsIm5pY2tuYW1lIjoiaW0gbWlua2kiLCJ1c2VybmFtZSI6ImFsc3JsODYyIiwiaWF0IjoxNzgwODkzMTU5LCJleHAiOjE3ODA4OTY3NTl9.gmv4h6TUgm3LBpP0My4EAY2v1es5kuiqvnM6LKiP-u0"
GRAPHQL_URL = "https://web-server.production.fruitsfamily.com/graphql"
headers_api = {"Authorization": TOKEN, "Content-Type": "application/json"}

query_products = """
query SeeSellerProducts($filter: ProductFilter!, $offset: Int, $limit: Int, $sort: String) {
  searchProducts(filter: $filter, offset: $offset, limit: $limit, sort: $sort, origin: "SELLER") {
    id
    createdAt
  }
}
"""

def get_monthly_uploads(seller_id):
    all_products = []
    offset = 0
    limit = 40

    while True:
        payload = {
            "operationName": "SeeSellerProducts",
            "query": query_products,
            "variables": {
                "filter": {"query": "", "sellerId": int(seller_id)},
                "sort": "NEW",
                "offset": offset,
                "limit": limit
            }
        }
        try:
            res = requests.post(GRAPHQL_URL, json=payload, headers=headers_api)
            data = res.json()
            if not data:
                break
            products = data.get('data', {}).get('searchProducts', [])
            if products is None:
                break
        except Exception as e:
            print(f"  API 에러: {e}, 건너뜀")
            break

        if not products:
            break
        all_products.extend(products)
        if len(products) < limit:
            break
        offset += limit

    monthly = defaultdict(int)
    for p in all_products:
        month = p['createdAt'][:7]
        monthly[month] += 1

    return monthly

seller_rows = supabase.table('fruits_sellers').select('*').execute().data
print(f"총 {len(seller_rows)}명 분석 시작...\n")

all_averages = []

for seller in seller_rows:
    print(f"[{seller['nickname']}] 분석 중...")
    monthly = get_monthly_uploads(seller['seller_id'])

    if not monthly:
        print(f"  → 데이터 없음\n")
        continue

    avg = round(statistics.mean(monthly.values()))
    max_month = max(monthly, key=monthly.get)
    min_month = min(monthly, key=monthly.get)

    # 출력
    print(f"  총 {sum(monthly.values())}개 상품")
    print(f"  월평균: {avg}개")
    print(f"  최다 업로드: {max_month} ({monthly[max_month]}개)")
    print(f"  최소 업로드: {min_month} ({monthly[min_month]}개)")
    for month, count in sorted(monthly.items()):
        print(f"    {month}: {count}개")

    # fruits_sellers만 업데이트
    supabase.table('fruits_sellers').update({
        "monthly_avg": avg,
        "max_month": max_month,
        "max_month_count": monthly[max_month],
        "total_products": sum(monthly.values()),
    }).eq('seller_id', seller['seller_id']).execute()

    print(f"  → 저장 완료!\n")
    all_averages.append(avg)

print("=== 전체 분석 완료 ===")
print(f"전체 평균: {round(statistics.mean(all_averages))}개/월")
print(f"중앙값: {round(statistics.median(all_averages))}개/월")