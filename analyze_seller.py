import requests
import json
import os
import statistics
from collections import defaultdict
from dotenv import load_dotenv

load_dotenv()

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
        res = requests.post(GRAPHQL_URL, json=payload, headers=headers_api)
        products = res.json().get('data', {}).get('searchProducts', [])

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

# 셀러 ID 입력
seller_id = input("셀러 ID 입력: ").strip()

print(f"\n[sellerId: {seller_id}] 분석 중...")
monthly = get_monthly_uploads(seller_id)

if not monthly:
    print("데이터 없음!")
else:
    avg = round(statistics.mean(monthly.values()))
    max_month = max(monthly, key=monthly.get)
    min_month = min(monthly, key=monthly.get)

    print(f"\n총 {sum(monthly.values())}개 상품")
    print(f"월평균: {avg}개")
    print(f"최다 업로드: {max_month} ({monthly[max_month]}개)")
    print(f"최소 업로드: {min_month} ({monthly[min_month]}개)")
    print(f"\n월별 업로드:")
    for month, count in sorted(monthly.items()):
        print(f"  {month}: {count}개")