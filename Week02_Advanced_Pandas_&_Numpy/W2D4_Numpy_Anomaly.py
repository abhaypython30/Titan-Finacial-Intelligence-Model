
import pandas as pd
import numpy as np

df = pd.read_csv('data/titan_ratios.csv')
df = df.sort_values('year').reset_index(drop=True)

# Single, consolidated metric list - includes 'inventory' for the new
# Titan-specific check, plus everything from Tata's Day4/Day5 versions.
metrics = ['sales', 'ebitda', 'net_profit', 'debt', 'selling_admin', 'debtors', 'inventory']

first_values = np.array([df[m].iloc[0] for m in metrics])
last_values = np.array([df[m].iloc[-1] for m in metrics])

# FIXED: dynamic year count instead of hardcoded 9
years = len(df) - 1
cagr_array = (last_values / first_values) ** (1 / years) - 1
cagr_dict = dict(zip(metrics, cagr_array))

print(f"CAGR computed over {years} years ({df['year'].iloc[0]} to {df['year'].iloc[-1]}):\n")
for metric, cagr in zip(metrics, cagr_array):
    print(f'{metric} CAGR: {cagr:.2%}')

# Flag: Debt growing faster than EBITDA
if cagr_dict['debt'] > cagr_dict['ebitda']:
    print('\n>> FLAG: Debt has grown faster than EBITDA over the period - '
          'rising leverage risk, worth investigating WHY.')

# Flag: Selling/admin costs outpacing sales
if cagr_dict['selling_admin'] > cagr_dict['sales']:
    print('\n>> FLAG: Selling & admin costs have grown faster than sales - '
          'cost discipline may be weakening.')

# NEW - Titan-specific: Inventory growing faster than Sales
if cagr_dict['inventory'] > cagr_dict['sales']:
    print('\n>> FLAG (Titan-specific): Inventory has grown faster than '
          'sales over the period - given gold/jewellery inventory is '
          'already a defining structural cost for this business, this '
          'signals working-capital efficiency may be deteriorating, not '
          'improving, over time. Worth investigating whether this is '
          'driven by gold price appreciation (inventory value rising '
          'without volume rising) or genuine overstocking.')
else:
    print('\nInventory growth has NOT outpaced sales growth - working '
          'capital efficiency on inventory appears stable or improving.')


# Single, consolidated definition - the original had this function
# defined twice, identically, in Day5.
def flag_anomalies(df, column, threshold=1.5):
    mean = df[column].mean()
    std = df[column].std()
    df[f'{column}_flag'] = (df[column] - mean).abs() > threshold * std
    return df[df[f'{column}_flag']][['year', column]]


print("\nYears requiring investigation - ROCE collapsed below normal range:")
print(flag_anomalies(df, 'roce'))

print("\nYears requiring investigation - cash conversion cycle lengthened unusually:")
print(flag_anomalies(df, 'cash_conversion_cycle'))

df.to_csv('data/titan_ratios.csv', index=False)