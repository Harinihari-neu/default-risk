# Notebooks

Naming convention — run in order:

1. `01_data_prep_exploration.ipynb` — load SQLite tables, sanity-check
   the label distribution, basic EDA (default rate by FICO band,
   LTV, vintage).
2. `02_modeling.ipynb` — logistic regression baseline, XGBoost/RF
   comparison, ROC-AUC / calibration / confusion matrix.
3. `03_scenario_analysis.ipynb` — FRED data pull, stress scenario
   simulation, baseline vs. stressed default rate comparison.
4. `04_report.ipynb` — final polished notebook: the 3-4 charts +
   plain-language takeaways, meant to be read standalone.

Keep exploratory/scratch work out of `04_report.ipynb` — it should
read cleanly for someone who didn't build the project.
