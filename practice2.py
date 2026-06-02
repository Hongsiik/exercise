import pandas as pd
import matplotlib
matplotlib.rc('font', family='Malgun Gothic')
matplotlib.rc('axes', unicode_minus=False)
import matplotlib.pyplot as plt

df = pd.read_csv(r'C:\Users\user\OneDrive\Desktop\idol_brand_fashion\charts.csv', encoding='latin1')


stroke_rank = df['weeks-on-board'].groupby(df['artist']).sum().sort_values(ascending=False).head(10)

print(stroke_rank)