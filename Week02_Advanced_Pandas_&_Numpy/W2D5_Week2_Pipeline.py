"""
Titan Company - Week 2, Day 5: Final Pipeline Build

Adapted and consolidated from Tata Motors' W2D5. This is the day that
produces the actual merged pipeline file everything in Week 4-6 reads
from - the equivalent of tata_pipeline_new.csv.

FIXED:
  - Output filename corrected to 'titan_pipeline_new.csv' to match the
    naming convention every Week4-6 script expects (PIPELINE_CSV
    constant). The original Tata code actually saved to
    'tata_pipeline_output.csv' - a different name than what Week4-6
    scripts were built to read - avoiding that same mismatch here.
  - Removed the dead 'pivot' table (computed but never used in the
    original Day5)
  - Removed the duplicate flag_anomalies() definition
  - years computed dynamically (len-1), not hardcoded
  - Sort by year applied consistently before positional logic

Everything computed in Days 1-4 (era, CAGR flags, anomaly flags) is
consolidated into ONE final dataframe and saved once, rather than each
day re-reading and re-saving titan_ratios.csv repeatedly.
"""

import pandas as pd
import numpy as np

df = pd.read_csv('data/titan_ratios.csv')
df = df.sort_values('year').reset_index(drop=True)


def assign_era(row):
    if row['year'] in [2020, 2021]:
        return 'COVID'
    elif row['year'] >= 2022:
        return 'Recovery'
    else:
        return 'Pre-COVID'


def flag_anomalies(df, column, threshold=1.5):
    mean = df[column].mean()
    std = df[column].std()
    df[f'{column}_flag'] = (df[column] - mean).abs() > threshold * std
    return df[df[f'{column}_flag']][['year', column]]


result = (
    df
    .assign(era=lambda d: d.apply(assign_era, axis=1))
    .sort_values('year')
    .reset_index(drop=True)
)

era_summary = result.groupby('era').agg(
    avg_sales_growth=('sales_growth', 'mean'),
    avg_ebitda_margin=('ebitda_margin', 'mean'),
    avg_roce=('roce', 'mean'),
    avg_ccc=('cash_conversion_cycle', 'mean'),
    avg_debt_to_ebitda=('debt_to_ebitda', 'mean'),
).round(4).reset_index()

print("Final Era Summary:")
print(era_summary)

# CAGR - consolidated single metric list (matches Day4)
metrics = ['sales', 'ebitda', 'net_profit', 'debt', 'selling_admin', 'debtors', 'inventory']
first_values = np.array([result[m].iloc[0] for m in metrics])
last_values = np.array([result[m].iloc[-1] for m in metrics])

years = len(result) - 1
cagr_array = (last_values / first_values) ** (1 / years) - 1
cagr_dict = dict(zip(metrics, cagr_array))

print(f"\nFinal CAGR summary ({years}-year period):")
for metric, cagr in zip(metrics, cagr_array):
    print(f'{metric} CAGR: {cagr:.2%}')

if cagr_dict['debt'] > cagr_dict['ebitda']:
    print('\n>> FLAG: Debt has grown faster than EBITDA over the period.')

if cagr_dict['selling_admin'] > cagr_dict['sales']:
    print('\n>> FLAG: Selling & admin costs have grown faster than sales.')

if cagr_dict['inventory'] > cagr_dict['sales']:
    print('\n>> FLAG (Titan-specific): Inventory has grown faster than sales.')

print("\nYears requiring investigation - ROCE anomalies:")
print(flag_anomalies(result, 'roce'))

print("\nYears requiring investigation - cash conversion cycle anomalies:")
print(flag_anomalies(result, 'cash_conversion_cycle'))

# FIXED: correct output filename matching what Week4-6 scripts expect
result.to_csv('data/titan_pipeline_new.csv', index=False)

# CHANGED: path updated to Titan's workbook
with pd.ExcelWriter('data/Titan project.xlsx', engine='openpyxl',
                     mode='a', if_sheet_exists='replace') as writer:
    result.to_excel(writer, sheet_name='Week2 Pipeline', index=False)
    era_summary.to_excel(writer, sheet_name='Week2 Era Summary', index=False)

print("\nDone. titan_pipeline_new.csv ready for Week 3.")