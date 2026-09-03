"""
Central configuration: file paths, vintages, and modeling parameters.

Keeping these in one place means the SQL loading scripts, feature
pipeline, and modeling notebooks all reference the same constants —
change a vintage or a window here, not in five different files.
"""

from pathlib import Path

# --- Paths -------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DATA_DIR = PROJECT_ROOT / "data" / "processed"
SQLITE_DB_PATH = PROCESSED_DATA_DIR / "fannie_mae.db"

# --- Vintages ------------------------------------------------------------
# NOTE: Fannie Mae's SF Loan Performance data is now distributed as a
# SINGLE combined file per vintage quarter (one row per loan per month,
# with static origination attributes like LTV/DTI/FICO repeated on
# every monthly row) — not as separate acquisition + performance files.
# Update filenames here if the portal names your downloads differently.
VINTAGES = {
    "2007Q1": {
        "loan_performance_file": RAW_DATA_DIR / "2007Q1.csv",
        "label": "crisis_era",
    },
    "2019Q1": {
        "loan_performance_file": RAW_DATA_DIR / "2019Q1.csv",
        "label": "stable_era",
    },
}

# --- Label construction ---------------------------------------------------
DEFAULT_WINDOW_MONTHS = 24          # observe default/prepay within N months of origination
DEFAULT_DELINQUENCY_THRESHOLD = 3   # "90+ days delinquent" -> delinquency status code >= 3
                                     # (confirm exact status code mapping against the glossary
                                     # before relying on this — Fannie's DLQ status field uses
                                     # specific codes, not raw days)

# --- Scenario analysis ------------------------------------------------
FRED_SERIES = {
    "mortgage_rate": "MORTGAGE30US",   # 30-year fixed mortgage rate
    "unemployment": "UNRATE",
}

STRESS_SCENARIO = {
    "rate_shock_bps": 200,     # +200 bps
    "home_price_decline_pct": 10,  # -10% -> raises effective LTV
}
