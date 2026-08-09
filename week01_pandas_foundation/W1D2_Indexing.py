import pandas as pd

# Read from titan_clean.csv
df = pd.read_csv('data/titan_clean.csv')


covid_years = df.loc[df["year"].isin([2020, 2021])]
print("\n covid_years\n", (covid_years))

last_row = df.iloc[-1]
print(last_row)


High_debt = df.loc[df['debt'] > 15000, ['year', 'debt']]
print(High_debt)