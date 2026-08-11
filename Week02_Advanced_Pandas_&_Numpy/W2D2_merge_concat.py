
import pandas as pd

df = pd.read_csv('data/titan_ratios.csv')
df = df.sort_values('year').reset_index(drop=True)

is_metrics = df[['year', 'sales', 'ebitda', 'ebit', 'net_profit']]
bs_metrics = df[['year', 'debtors', 'inventory', 'debt', 'capital_employed']]

merged = pd.merge(is_metrics, bs_metrics, on='year', how='left', validate='one_to_one')

print('Shape before merge:', is_metrics.shape, bs_metrics.shape)
print('Shape after merge:', merged.shape)
assert merged.shape[0] == is_metrics.shape[0], 'Row count changed - merge bug!'

pre_2020 = df[df['year'] < 2020]
post_2020 = df[df['year'] >= 2020]
combined = pd.concat([pre_2020, post_2020])

print('\nOriginal shape:', df.shape)
print('Concat shape:', combined.shape)
assert combined.shape[0] == df.shape[0], 'Concat changed row count!'

print('\nAll checks passed - merge and concat operations are safe to use '
      'on this dataset.')

df.to_csv('data/titan_ratios.csv', index=False)