import pandas as pd

df = pd.read_csv('data/titan_clean.csv')



# Calculation of COGS for Gross profit and EBITDA Calculation
df['cogs'] = (
    df['raw_material_cost']
    + df['power_fuel']
    + df['other_mfr_exp']
    + df['employee_cost']
    - df['change_in_inventory']
)

# EBITDA CALC
df['ebitda'] = (
    df['sales'] - df['cogs']
    - df['selling_admin']
    - df['other_expenses']
)
print('\n', df['ebitda'], '\n')

# EBIT CALC
df['ebit'] = df['ebitda'] - df['depreciation']
print(df['ebit'])

# Growth ratios
df['sales_growth'] = df['sales'].pct_change().round(4)
df['ebitda_growth'] = df['ebitda'].pct_change().round(4)
df['ebit_growth'] = df['ebit'].pct_change().round(4)
df['net_profit_growth'] = df['net_profit'].pct_change().round(4)
print(df[['sales_growth', 'ebit_growth', 'ebitda_growth', 'net_profit_growth']])

# Gross profit calculation
df['gross_profit'] = df['sales'] - df['cogs']
print(df['gross_profit'])

# Margin ratios
df['gross_margin'] = (df['gross_profit'] / df['sales']).round(4)
df['ebitda_margin'] = (df['ebitda'] / df['sales']).round(4)
df['ebit_margin'] = (df['ebit'] / df['sales']).round(4)
df['ebt_margin'] = (df['ebt'] / df['sales']).round(4)
df['net_margin'] = (df['net_profit'] / df['sales']).round(4)

print(df[['gross_margin', 'ebitda_margin', 'ebit_margin', 'ebt_margin', 'net_margin']])

df.to_csv('data/titan_clean.csv', index=False)