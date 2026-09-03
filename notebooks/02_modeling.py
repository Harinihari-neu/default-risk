"""
Phase 3, part 2: logistic regression baseline vs. XGBoost, evaluated
with ROC-AUC, confusion matrix, and calibration — not accuracy, since
defaults are ~1.5% of the data (a model that always predicts "no
default" would score 98.5% accuracy while being useless).
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    roc_auc_score, roc_curve, confusion_matrix,
    classification_report
)
from sklearn.calibration import calibration_curve
import xgboost as xgb

df = pd.read_csv('data/processed/training_data_clean.csv')
print(f"Loaded {len(df):,} rows")

# %% Feature prep
# Categorical columns -> one-hot; numeric columns used as-is.
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
print(f"Train: {len(X_train):,} rows ({y_train.mean():.4f} default rate)")
print(f"Test:  {len(X_test):,} rows ({y_test.mean():.4f} default rate)")

# %% Baseline: Logistic Regression
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

logreg = LogisticRegression(max_iter=1000, class_weight='balanced', random_state=42)
logreg.fit(X_train_scaled, y_train)

logreg_probs = logreg.predict_proba(X_test_scaled)[:, 1]
logreg_auc = roc_auc_score(y_test, logreg_probs)
print(f"\n=== Logistic Regression ===")
print(f"ROC-AUC: {logreg_auc:.4f}")
print(classification_report(y_test, (logreg_probs >= 0.5).astype(int)))

# %% Comparison: XGBoost
scale_pos_weight = (y_train == 0).sum() / (y_train == 1).sum()
xgb_model = xgb.XGBClassifier(
    n_estimators=200, max_depth=5, learning_rate=0.1,
    scale_pos_weight=scale_pos_weight, random_state=42,
    eval_metric='auc'
)
xgb_model.fit(X_train, y_train)

xgb_probs = xgb_model.predict_proba(X_test)[:, 1]
xgb_auc = roc_auc_score(y_test, xgb_probs)
print(f"\n=== XGBoost ===")
print(f"ROC-AUC: {xgb_auc:.4f}")
print(classification_report(y_test, (xgb_probs >= 0.5).astype(int)))

# %% Chart 1: ROC curves, both models
fig, ax = plt.subplots(figsize=(7, 6))
for name, probs, auc in [('Logistic Regression', logreg_probs, logreg_auc), ('XGBoost', xgb_probs, xgb_auc)]:
    fpr, tpr, _ = roc_curve(y_test, probs)
    ax.plot(fpr, tpr, label=f'{name} (AUC = {auc:.3f})')
ax.plot([0, 1], [0, 1], 'k--', alpha=0.3, label='Random')
ax.set_xlabel('False Positive Rate')
ax.set_ylabel('True Positive Rate')
ax.set_title('ROC Curve: Logistic Regression vs. XGBoost')
ax.legend()
plt.tight_layout()
plt.savefig('reports/figures/roc_curve.png', dpi=150)
print("\nSaved: reports/figures/roc_curve.png")

# %% Chart 2: Feature importance (XGBoost) vs. coefficients (Logistic)
fig, axes = plt.subplots(1, 2, figsize=(14, 6))

# XGBoost feature importance (top 15)
importances = pd.Series(xgb_model.feature_importances_, index=X.columns).sort_values(ascending=False).head(15)
axes[0].barh(importances.index[::-1], importances.values[::-1])
axes[0].set_title('XGBoost: Top 15 Feature Importances')
axes[0].set_xlabel('Importance')

# Logistic regression coefficients (top 15 by absolute value)
coefs = pd.Series(logreg.coef_[0], index=X.columns)
top_coefs = coefs.reindex(coefs.abs().sort_values(ascending=False).head(15).index)
colors = ['red' if v > 0 else 'blue' for v in top_coefs.values[::-1]]
axes[1].barh(top_coefs.index[::-1], top_coefs.values[::-1], color=colors)
axes[1].set_title('Logistic Regression: Top 15 Coefficients\n(red = increases default risk, blue = decreases)')
axes[1].set_xlabel('Coefficient (standardized)')

plt.tight_layout()
plt.savefig('reports/figures/feature_importance_comparison.png', dpi=150)
print("Saved: reports/figures/feature_importance_comparison.png")

# %% Chart 3: Calibration curve
fig, ax = plt.subplots(figsize=(7, 6))
for name, probs in [('Logistic Regression', logreg_probs), ('XGBoost', xgb_probs)]:
    frac_pos, mean_pred = calibration_curve(y_test, probs, n_bins=10)
    ax.plot(mean_pred, frac_pos, marker='o', label=name)
ax.plot([0, 1], [0, 1], 'k--', alpha=0.3, label='Perfectly calibrated')
ax.set_xlabel('Mean Predicted Probability')
ax.set_ylabel('Fraction of Actual Positives')
ax.set_title('Calibration Curve')
ax.legend()
plt.tight_layout()
plt.savefig('reports/figures/calibration_curve.png', dpi=150)
print("Saved: reports/figures/calibration_curve.png")

# %% Confusion matrices
print("\n=== Confusion Matrix: Logistic Regression (threshold 0.5) ===")
print(confusion_matrix(y_test, (logreg_probs >= 0.5).astype(int)))
print("\n=== Confusion Matrix: XGBoost (threshold 0.5) ===")
print(confusion_matrix(y_test, (xgb_probs >= 0.5).astype(int)))

print("\nDone. Four charts saved to reports/figures/.")