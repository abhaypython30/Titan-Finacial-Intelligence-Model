
import pandas as pd

df = pd.read_csv("data/titan_ratios.csv")
df = df.sort_values('year').reset_index(drop=True)


def assign_era(row):
    if row['year'] in [2020, 2021]:
        return 'COVID'
    elif row['year'] >= 2022:
        return 'Recovery'
    else:
        return 'Pre-COVID'


df['era'] = df.apply(assign_era, axis=1)

era_summary = df.groupby('era').agg(
    avg_sales_growth=('sales_growth', 'mean'),
    avg_ebitda_margin=('ebitda_margin', 'mean'),
    avg_roce=('roce', 'mean'),
    avg_ccc=('cash_conversion_cycle', 'mean'),
    avg_debt_to_ebitda=('debt_to_ebitda', 'mean')
).round(4).reset_index()

print("Era Summary:")
print(era_summary)
print("\nReview the above before treating COVID/Recovery boundaries as "
      "final for Titan - adjust assign_era() if the numbers suggest a "
      "different split makes more sense for a retail business." )
df.to_csv('data/titan_ratios.csv', index=False)

