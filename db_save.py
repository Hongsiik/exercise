import sqlite3
import pandas as pd
from datetime import datetime

conn = sqlite3.connect('musinsa.db')
cursor = conn.cursor()

cursor.execute('''
    CREATE TABLE IF NOT EXISTS ranking (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        브랜드 TEXT,
        상품명 TEXT,
        가격 INTEGER,
        수집날짜 TEXT
    )
''')

# 오늘 날짜
today = datetime.now().strftime('%Y-%m-%d')

# 오늘 데이터 이미 있으면 저장 안 함
existing = pd.read_sql(f"SELECT COUNT(*) as cnt FROM ranking WHERE 수집날짜 = '{today}'", conn)

if existing['cnt'][0] > 0:
    print(f'오늘({today}) 데이터 이미 있음. 저장 건너뜀.')
else:
    df = pd.read_csv('musinsa_ranking.csv')
    df['수집날짜'] = today
    df.to_sql('ranking', conn, if_exists='append', index=False)
    print(f'{len(df)}개 데이터 DB 저장 완료!')

# 조회
result = pd.read_sql('SELECT * FROM ranking WHERE 가격 <= 20000', conn)
print(result)

conn.close()