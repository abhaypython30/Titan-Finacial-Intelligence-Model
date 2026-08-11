import pandas as pd
import numpy as np

df = pd.read_csv('data/titan_clean.csv')

# base derived columns
df['ebitda'] = (
    df['sales'] - df['cogs']
    - df['selling_admin']
    - df['other_expenses']
)
print('\n', df['ebitda'], '\n')

df['ebit'] = df['ebitda'] - df['depreciation']
print(df['ebit'])

df['cogs'] = (
    df['raw_material_cost']
    + df['power_fuel']
    + df['other_mfr_exp']
    + df['employee_cost']
    - df['change_in_inventory']
)

df['gross_profit'] = df['sales'] - df['cogs']
print(df['gross_profit'])

df['capital_employed'] = df[['equity_share_cap', 'reserves', 'debt']].sum(axis=1)
df['capital_turnover'] = (df['sales'] / df['capital_employed']).round(2)

df['avg_debtors'] = (df['debtors'] + df['debtors'].shift(1)) / 2

# Growth ratios
df['sales_growth'] = df['sales'].pct_change().round(4)
df['ebitda_growth'] = df['ebitda'].pct_change().round(4)
df['ebit_growth'] = df['ebit'].pct_change().round(4)
df['net_profit_growth'] = df['net_profit'].pct_change().round(4)

# Margin ratios
df['gross_margin'] = (df['gross_profit'] / df['sales']).round(4)
df['ebitda_margin'] = (df['ebitda'] / df['sales']).round(4)
df['ebit_margin'] = (df['ebit'] / df['sales']).round(4)
df['ebt_margin'] = (df['ebt'] / df['sales']).round(4)
df['net_margin'] = (df['net_profit'] / df['sales']).round(4)

# Turnover Ratios
df['debtor_turnover'] = (df['sales'] / df['avg_debtors']).round(2)
df['inventory_turnover'] = (df['sales'] / df['inventory']).round(2)
df['creditor_turnover'] = (df['sales'] / df['payables']).round(2)
df['fixed_asset_turnover'] = (df['sales'] / df['fixed_assets']).round(2)

# Day Metrics
# NOTE: expect Titan's inventory_days to be MUCH higher 
# gold/jewellery inventory ties  to sales 

df['debtor_days'] = (365 / df['debtor_turnover']).round(0)
df['payables_days'] = (365 / df['creditor_turnover']).round(0)
df['inventory_days'] = (365 / df['inventory_turnover']).round(0)
df['cash_conversion_cycle'] = (df['debtor_days'] + df['inventory_days'] - df['payables_days']).round(0)


def clean_financials(data):
    data = data.copy()
    data['sales'] = pd.to_numeric(data['sales'], errors='coerce')
    data['sales'] = data['sales'].ffill()
    data = data.sort_values('year').reset_index(drop=True)
    return data


clean_df = clean_financials(df)
assert clean_df['sales'].isnull().sum() == 0

print(clean_df)
print("Cleaning check passed: zero NaNs in sales")

# ROCE, interest coverage, credit signal
df['capital_turnover'] = (df['sales'] / df['capital_employed']).round(2)
df['roce'] = (df['ebit'] / df['capital_employed']).round(4)
df['interest_coverage'] = (df['ebit'] / df['interest']).round(2)
df['debt_to_ebitda'] = (df['debt'] / df['ebitda']).round(1)


def credit_signal(row):
    # NOTE: these thresholds (Stress>6, Watch>3) were reasonable defaults
    # for Tata Motors' auto-sector leverage profile. Titan's leverage is
    # structurally lower (asset-light retail) - sanity-check whether these
    # same cutoffs make sense for Titan, or whether they'd label a
    # perfectly normal Titan leverage level as "Watch"/"Stress" simply
    # because the sector norm is different. Worth revisiting once you see
    # the actual output below, not something to silently trust.
    ratio = row['debt_to_ebitda']
    if ratio > 3:
        return 'Stress'
    elif ratio > 1.5:
        return 'Watch'
    else:
        return 'Healthy'


df['credit'] = df.apply(credit_signal, axis=1)
print(df[['year', 'ebitda_margin', 'net_margin', 'roce', 'interest_coverage', 'credit']])

# SUMMARY STATS
summary = df[['sales_growth', 'ebitda_margin', 'net_margin',
              'debtor_turnover', 'roce']].agg(['mean', 'median']).round(4)
print("\nSummary stats:\n", summary)

# EXPORT - write to Excel "Python Output" tab
with pd.ExcelWriter('G:/Titan/data/Titan Project.xlsx', engine='openpyxl',
                     mode='a', if_sheet_exists='replace') as writer:
    df.to_excel(writer, sheet_name='Python Output', index=False)
    summary.to_excel(writer, sheet_name='Python Summary')

print("\nDone. Check Python Output tab - verify numbers against Ratio Analysis tab.")

df = df.drop(columns=['ebitda_check', 'ebt_check'], errors='ignore')
# CHANGED: output filename to titan_ratios.csv
df.to_csv('data/titan_ratios.csv', index=False)
