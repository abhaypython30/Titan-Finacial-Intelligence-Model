import pandas as pd

# CHANGED: file path to Titan's workbook
df = pd.read_excel("data/Titan Project.xlsx", sheet_name="Data Sheet")
df = df.set_index('metric_name').T.reset_index()
df = df.rename(columns={'index': 'year'})
df.columns = [c.lower().strip() for c in df.columns]

# pbt to ebt 
df = df.rename(columns={'pbt': 'ebt'})

# Changed time style to only year
df['year'] = pd.to_datetime(df['year']).dt.year
print(df)

# Practice of Commands
print('\nshape: \n', df.shape)
print('\nHead: \n', df.head())
print('\nInfo: \n', df.info())
print('\nData Types: \n', df.dtypes)
print('\nNull Values: \n', df.isnull().sum())

print("\n", df.columns.to_list())

# Practise of formulas
max_sales = df.loc[df["sales"].idxmax(), 'year']
print(f' \n Maximum sale year is; {max_sales}')


df.to_csv('data/titan_clean.csv', index=False)
print("\nSaved clean csv. From next session read this file directly")