import requests
from bs4 import BeautifulSoup
import pandas as pd

df = pd.read_csv('books_all.csv')

#1
df['가격'] = df['가격'].str.replace('£', '').astype(float)

#평균가격
print(df['가격'].mean())
print('----------------------------------------')

#3 가장 비싼 책 Top 10
result = df.sort_values(by='가격', ascending=False).head(10)
print(result)