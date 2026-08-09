import pandas as pd
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import get_column_with_fallback

df = pd.read_csv('data/titan_clean.csv')

# Column Fallback Defense

# Debtor Turnover - credit_sales not disclosed, fallback to sales
credit_sales_col = get_column_with_fallback(
    df, preferred_col='credit_sales', fallback_col='sales',
    ratio_name='debtor_turnover'
)

# Inventory Turnover - same Sales-proxy logic applies
sales_col_for_inv = get_column_with_fallback(
    df, preferred_col='credit_sales', fallback_col='sales',
    ratio_name='inventory_turnover'
)

# Creditor Turnover - NOTE:  Titan's sheet HAS a direct
# 'payables' column, so this fallback will use 'payables' directly and
# never actually need the 'other_liabilities' fallback. 

payables_col = get_column_with_fallback(
    df, preferred_col='payables', fallback_col='other_liabilities',
    ratio_name='creditor_turnover'
)

# Turnover Ratios Calculation
df['avg_debtors'] = (df['debtors'] + df['debtors'].shift(1)) / 2

df['debtor_turnover'] = (credit_sales_col / df['avg_debtors']).round(2)
df['inventory_turnover'] = (sales_col_for_inv / df['inventory']).round(2)
df['creditor_turnover'] = (df['sales'] / payables_col).round(2)
df['fixed_asset_turnover'] = (df['sales'] / df['fixed_assets']).round(2)

# Calculating Capital Employed 
df['capital_employed'] = df[['equity_share_cap', 'reserves', 'debt']].sum(axis=1)
df['capital_turnover'] = (df['sales'] / df['capital_employed']).round(2)

# Day Metrics
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

print(df[['year', 'debtor_turnover', 'debtor_days', 'inventory_days', 'payables_days', 'cash_conversion_cycle']])

# FIXED: added index=False (original Tata W1D4 was also missing this)
df.to_csv('data/titan_clean.csv', index=False)