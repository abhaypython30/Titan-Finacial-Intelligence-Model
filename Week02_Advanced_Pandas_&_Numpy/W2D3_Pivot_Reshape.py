
import pandas as pd

df = pd.read_csv('data/titan_ratios.csv')
df = df.sort_values('year').reset_index(drop=True)

# MELT - wide to long
long_df = df.melt(
    id_vars='year',
    value_vars=['gross_margin', 'ebitda_margin', 'roce',
                'cash_conversion_cycle', 'debt_to_ebitda'],
    var_name='metric', value_name='value'
)

print(long_df.head(10))

# PIVOT - back to wide, but metric-as-row this time
pivot = long_df.pivot_table(index='metric', columns='year', values='value')

print("\nPivot table (matches Excel Ratio Analysis layout):")
print(pivot)