"""
Phase 4: macro stress scenario analysis.

Pulls historical mortgage rate + unemployment series from FRED for
context, then simulates "rates +200bps, home prices -10%" by:
  - adding 200bps to each loan's interest rate feature
  - inflating each loan's LTV to reflect the home price decline
    (if property value drops X%, effective LTV = orig_ltv / (1 - X/100),
    since the loan balance is unchanged but the collateral value fell)

Re-scores the portfolio with the trained XGBoost model under both the
baseline and stressed inputs, and compares the resulting default rate.
"""

import os
import pandas as pd
import matplotlib.pyplot as plt
from dotenv import load_dotenv
from fredapi import Fred
from sklearn.model_selection import train_test_split
import xgboost as xgb

load_dotenv()
fred = Fred(api_key=os.environ["FRED_API_KEY"])

# %% Pull FRED series for context
mortgage_rate = fred.get_series('MORTGAGE30US')
unemployment = fred.get_series('UNRATE')

print(f"Most recent 30-year mortgage rate: {mortgage_rate.iloc[-1]:.2f}% (as of {mortgage_rate.index[-1].date()})")
print(f"Most recent unemployment rate: {unemployment.iloc[-1]:.2f}% (as of {unemployment.index[-1].date()})")

fig, axes = plt.subplots(2, 1, figsize=(10, 7), sharex=True)
axes[0].plot(mortgage_rate.index, mortgage_rate.values, color='steelblue')
axes[0].set_title('30-Year Fixed Mortgage Rate (FRED: MORTGAGE30US)')
axes[0].set_ylabel('Rate (%)')
axes[1].plot(unemployment.index, unemployment.values, color='indianred')
axes[1].set_title('Unemployment Rate (FRED: UNRATE)')
axes[1].set_ylabel('Rate (%)')
plt.tight_layout()
plt.savefig('reports/figures/fred_context_series.png', dpi=150)
print("Saved: reports/figures/fred_context_series.png")

# %% Reload cleaned training data and retrain XGBoost on the full set
# (Phase 3 already validated this model; here we retrain for use in
# scoring the scenario rather than re-deriving performance metrics.)
df = pd.read_csv('data/processed/training_data_clean.csv')

categorical_cols = [
    'loan_purpose', 'occupancy_status', 'property_type',
    'property_state', 'first_time_home_buyer_indicator', 'amortization_type'
]
numeric_cols = [
    'borrower_credit_score', 'orig_ltv', 'orig_cltv', 'dti',
    'number_of_units', 'number_of_borrowers', 'original_loan_term',
    'original_interest_rate'
]

X = pd.get_dummies(df[categorical_cols + numeric_cols], columns=categorical_cols, drop_first=True)
X = X.fillna(X.median(numeric_only=True))
y = df['is_default']

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

scale_pos_weight = (y_train == 0).sum() / (y_train == 1).sum()
xgb_model = xgb.XGBClassifier(
    n_estimators=200, max_depth=5, learning_rate=0.1,
    scale_pos_weight=scale_pos_weight, random_state=42,
    eval_metric='auc'
)
xgb_model.fit(X_train, y_train)

# NOTE: the classification model above uses scale_pos_weight to
# improve separation between classes (what AUC measures) — but that
# same reweighting distorts the ABSOLUTE predicted probabilities,
# skewing them well above the true ~1.5% base default rate. For the
# scenario analysis we care about the actual portfolio-level default
# rate, not just ranking loans by relative risk, so we train a
# second, unweighted model here specifically for calibrated
# probability estimates. This is a deliberate, explainable modeling
# choice — worth calling out in the write-up: classification
# performance and calibrated probability estimation can require
# different training setups when classes are this imbalanced.
xgb_model_calibrated = xgb.XGBClassifier(
    n_estimators=200, max_depth=5, learning_rate=0.1,
    random_state=42, eval_metric='auc'
)
xgb_model_calibrated.fit(X_train, y_train)

# %% Baseline portfolio-level default rate (on the test set — same
# loans, unstressed)
baseline_probs = xgb_model_calibrated.predict_proba(X_test)[:, 1]
baseline_default_rate = baseline_probs.mean()
print(f"\nBaseline predicted portfolio default rate: {baseline_default_rate:.4%}")

# %% Build the stressed scenario: +200bps rate, -10% home prices
RATE_SHOCK_PCT = 2.0       # +200 bps = +2.0 percentage points
HOME_PRICE_DECLINE_PCT = 10.0

X_stressed = X_test.copy()
X_stressed['original_interest_rate'] = X_stressed['original_interest_rate'] + RATE_SHOCK_PCT
X_stressed['orig_ltv'] = X_stressed['orig_ltv'] / (1 - HOME_PRICE_DECLINE_PCT / 100)
# Cap stressed LTV at 200 (Fannie's own glossary treats values above
# this as effectively unbounded/null) to avoid unrealistic extremes
# dominating the average.
X_stressed['orig_ltv'] = X_stressed['orig_ltv'].clip(upper=200)

stressed_probs = xgb_model_calibrated.predict_proba(X_stressed)[:, 1]
stressed_default_rate = stressed_probs.mean()
print(f"Stressed predicted portfolio default rate:  {stressed_default_rate:.4%}")
print(f"\nRelative increase: {(stressed_default_rate / baseline_default_rate - 1):.1%}")

# %% Chart: baseline vs. stressed default rate
fig, ax = plt.subplots(figsize=(6, 6))
bars = ax.bar(
    ['Baseline', f'Stressed\n(+{RATE_SHOCK_PCT}pp rate,\n-{HOME_PRICE_DECLINE_PCT}% HPI)'],
    [baseline_default_rate * 100, stressed_default_rate * 100],
    color=['steelblue', 'indianred']
)
for bar in bars:
    height = bar.get_height()
    ax.annotate(f'{height:.2f}%', xy=(bar.get_x() + bar.get_width() / 2, height),
                xytext=(0, 5), textcoords='offset points', ha='center', fontweight='bold')
ax.set_ylabel('Predicted Portfolio Default Rate (%)')
ax.set_title('Baseline vs. Stressed Scenario: Predicted Default Rate')
plt.tight_layout()
plt.savefig('reports/figures/baseline_vs_stressed.png', dpi=150)
print("\nSaved: reports/figures/baseline_vs_stressed.png")

print("\nDone.")