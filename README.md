markdown
# Mortgage Default Risk Modeling & Macro Stress Testing

Loan-level default risk model built on Fannie Mae's public
Single-Family Loan Performance Dataset, with a macro scenario overlay
("what happens to portfolio default rates if rates spike or home
prices fall?").

## Key results

- **577,788 loans** modeled across two vintages (2007Q1 crisis-era,
  2019Q1 stable-era), after excluding 17,069 loans whose apparent
  "default" was actually a COVID-19 forbearance reporting artifact
  (see Finding #1 below).
- **Logistic Regression AUC: 0.864** | **XGBoost AUC: 0.866** — the
  simple, interpretable baseline captures nearly all the predictive
  signal that the more complex model does.
- **Stress scenario** (+200bps mortgage rate, -10% home prices):
  predicted portfolio default rate rises from a calibrated baseline
  of **1.50% to 3.79%** — a **152.7% relative increase**.

Full write-up with charts: [`notebooks/04_final_report.ipynb`](notebooks/04_final_report.ipynb)

## Motivation

Uses the same category of loan-level data Fannie Mae's own credit risk
teams work with — origination characteristics (FICO, LTV, DTI,
occupancy, geography) — to predict 24-month default risk, then
stress-tests the trained model against an adverse macro scenario
grounded in real historical rate data pulled from FRED.

## Vintages used

- **2007 Q1** — crisis-era origination cohort
- **2019 Q1** — stable-era cohort (24-month window happens to overlap
  COVID-era forbearance — see Finding #1)

## Two findings worth highlighting

**1. COVID forbearance contaminated the 2019Q1 default label.** Initial
label construction showed 2019Q1 with a *higher* default rate than the
2007 crisis vintage — backwards from what history predicts. Root cause:
94% of what looked like "2019Q1 defaults" were loans in CARES Act
forbearance, reported with elevated delinquency codes despite not
being in genuine financial distress (their 24-month mark lands
~Q1 2021, peak forbearance activity). These were split into a
separate `covid_forbearance` outcome and excluded from the binary
classification target. See `docs/decisions.md` for the full
investigation.

**2. `scale_pos_weight` distorts absolute probability, not just
threshold behavior.** The classification model uses `scale_pos_weight`
to handle the ~1.5% base default rate — great for ROC-AUC and recall,
but it also inflates raw predicted probabilities (averaging to an
implausible 26.6% predicted default rate against a true ~1.5% base
rate). For the scenario analysis, which needs the *absolute* portfolio
default rate rather than a relative risk ranking, a separate unweighted
model was trained specifically for calibrated probability estimates.

## Repo structure

data/
raw/ # Original Fannie Mae SF Loan Performance files, single combined file per quarter (not committed — see data/raw/README.md)
processed/ # SQLite db + cleaned CSV export used for modeling
sql/ # SQL pipeline: indexing, label construction, feature table, vintage combination
notebooks/ # Analysis scripts + final report notebook
src/ # Data loading module (load_data.py) + config
reports/ # Exported figures used in the final report
docs/ # Decisions log — the full history of choices, bugs found, and fixes


## Pipeline

1. **Data prep (SQL)** — load the single combined SF Loan Performance
   file per vintage into SQLite (~28M raw loan-month rows), collapse
   monthly history into a single 24-month outcome label per loan
   (`sql/00`–`sql/03`).
2. **Modeling (Python)** — logistic regression baseline vs. XGBoost,
   evaluated on ROC-AUC, calibration, and confusion matrix (not
   accuracy, given ~1.5% default rate).
3. **Scenario analysis** — pull mortgage rate + unemployment series
   from FRED, simulate a stress scenario (+200bps rate, -10% home
   prices → higher effective LTV), and re-score the portfolio with a
   calibrated model.
4. **Report** — `notebooks/04_final_report.ipynb`, with charts and
   written takeaways per section.

## Status

✅ Complete. See `docs/decisions.md` for the full history of decisions,
bugs found and fixed, and open ideas for extension.

## Setup

```bash
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

You'll also need a free [FRED API key](https://fred.stlouisfed.org/docs/api/api_key.html)
saved in a `.env` file at the repo root:

FRED_API_KEY=your_key_here


## Data source

Fannie Mae Single-Family Loan Performance Dataset, via the
[Data Dynamics portal](https://datadynamics.fanniemae.com/) (free
registration required). Raw files are not committed to this repo —
see `data/raw/README.md` for download instructions.

Save this over your existing README.md at the repo root, then commit and push:

git add README.md
git commit -m "Update README with final results and key findings"
git push