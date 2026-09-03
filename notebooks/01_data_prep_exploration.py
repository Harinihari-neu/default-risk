"""
Phase 3, part 1: load training_data, exclude ambiguous COVID
forbearance loans, and run baseline exploratory checks before
modeling.

This is a plain script for now — once the plots look right, convert
this into notebooks/01_data_prep_exploration.ipynb by pasting each
section into its own cell (or open this file directly in Jupyter/VS
Code, which can run .py files cell-by-cell using '# %%' markers).
"""

import sqlite3

import matplotlib.pyplot as plt
import pandas as pd

conn = sqlite3.connect(r"data/processed/fannie_mae.db")
df = pd.read_sql("SELECT * FROM training_data", conn)
conn.close()

print(f"Total rows loaded: {len(df):,}")
print(df['outcome'].value_counts())

# %% Exclude ambiguous COVID forbearance loans — see docs/decisions.md
df_model = df[df['outcome'] != 'covid_forbearance'].copy()
df_model['is_default'] = (df_model['outcome'] == 'default').astype(int)

print(f"\nModeling rows after exclusion: {len(df_model):,}")
print(df_model['is_default'].value_counts(normalize=True))

# %% Default rate by FICO band — first EDA chart
df_model['fico_band'] = pd.cut(
    df_model['borrower_credit_score'],
    bins=[0, 620, 660, 700, 740, 780, 850],
    labels=['<620', '620-659', '660-699', '700-739', '740-779', '780+']
)

fico_default_rate = (
    df_model.groupby(['vintage', 'fico_band'])['is_default']
    .mean()
    .reset_index()
)
print("\nDefault rate by FICO band and vintage:")
print(fico_default_rate)

fig, ax = plt.subplots(figsize=(9, 5))
for vintage in df_model['vintage'].unique():
    subset = fico_default_rate[fico_default_rate['vintage'] == vintage]
    ax.plot(subset['fico_band'].astype(str), subset['is_default'] * 100, marker='o', label=vintage)
ax.set_xlabel('FICO Band')
ax.set_ylabel('Default Rate (%)')
ax.set_title('24-Month Default Rate by FICO Band and Vintage')
ax.legend(title='Vintage')
plt.tight_layout()
plt.savefig('reports/figures/default_rate_by_fico.png', dpi=150)
print("\nSaved: reports/figures/default_rate_by_fico.png")

# %% Default rate by LTV band — second EDA chart
df_model['ltv_band'] = pd.cut(
    df_model['orig_ltv'],
    bins=[0, 60, 70, 80, 90, 95, 100, 110],
    labels=['<=60', '61-70', '71-80', '81-90', '91-95', '96-100', '>100']
)

ltv_default_rate = (
    df_model.groupby(['vintage', 'ltv_band'])['is_default']
    .mean()
    .reset_index()
)
print("\nDefault rate by LTV band and vintage:")
print(ltv_default_rate)

fig, ax = plt.subplots(figsize=(9, 5))
for vintage in df_model['vintage'].unique():
    subset = ltv_default_rate[ltv_default_rate['vintage'] == vintage]
    ax.plot(subset['ltv_band'].astype(str), subset['is_default'] * 100, marker='o', label=vintage)
ax.set_xlabel('Original LTV Band')
ax.set_ylabel('Default Rate (%)')
ax.set_title('24-Month Default Rate by LTV Band and Vintage')
ax.legend(title='Vintage')
plt.tight_layout()
plt.savefig('reports/figures/default_rate_by_ltv.png', dpi=150)
print("\nSaved: reports/figures/default_rate_by_ltv.png")

# %% Save the cleaned modeling dataset for the next script (logistic regression)
df_model.to_csv('data/processed/training_data_clean.csv', index=False)
print(f"\nSaved cleaned modeling dataset: data/processed/training_data_clean.csv ({len(df_model):,} rows)")