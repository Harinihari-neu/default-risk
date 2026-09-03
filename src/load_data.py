"""
Load raw Fannie Mae Single-Family Loan Performance files into SQLite.

Each vintage quarter is one flat, pipe-delimited file with NO header
row: one row per loan per month, static origination attributes (LTV,
DTI, FICO, occupancy, etc.) repeated on every monthly row for a given
loan, and dynamic attributes (delinquency status, zero balance code,
current UPB) changing month to month.

Column order below is VERIFIED against Fannie Mae's official combined
CAS/CIRT/SF "Glossary and File Layout" (113 total field positions,
matching the 113 columns confirmed in the actual downloaded file via:
  (Get-Content .\\2007Q1.csv -TotalCount 1) -split '\\|' | Measure-Object
Fields not applicable to the SF Loan Performance dataset (marked NA
in the glossary's "Single-Family (SF) Loan Performance" column) are
still present as columns — they're simply always blank/null for SF
data. Those are flagged below with a comment.
"""

import sqlite3
from pathlib import Path

import pandas as pd

from config import SQLITE_DB_PATH, VINTAGES

LOAN_PERFORMANCE_COLUMNS = [
    "reference_pool_id",  # not used by SF — always blank/null
    "loan_identifier",
    "monthly_reporting_period",
    "channel",
    "seller_name",
    "servicer_name",
    "master_servicer",  # not used by SF — always blank/null
    "original_interest_rate",
    "current_interest_rate",
    "original_upb",
    "upb_at_issuance",  # not used by SF — always blank/null
    "current_actual_upb",
    "original_loan_term",
    "origination_date",
    "first_payment_date",
    "loan_age",
    "remaining_months_to_legal_maturity",
    "remaining_months_to_maturity",
    "maturity_date",
    "orig_ltv",
    "orig_cltv",
    "number_of_borrowers",
    "dti",
    "borrower_credit_score",
    "co_borrower_credit_score",
    "first_time_home_buyer_indicator",
    "loan_purpose",
    "property_type",
    "number_of_units",
    "occupancy_status",
    "property_state",
    "msa",
    "zip_code_short",
    "mortgage_insurance_percentage",
    "amortization_type",
    "prepayment_penalty_indicator",
    "interest_only_loan_indicator",
    "interest_only_first_principal_and_interest_payment_date",
    "months_to_amortization",
    "current_loan_delinquency_status",
    "loan_payment_history",
    "modification_flag",
    "mortgage_insurance_cancellation_indicator",  # not used by SF — always blank/null
    "zero_balance_code",
    "zero_balance_effective_date",
    "upb_at_the_time_of_removal",
    "repurchase_date",  # not used by SF — always blank/null
    "scheduled_principal_current",  # not used by SF — always blank/null
    "total_principal_current",
    "unscheduled_principal_current",  # not used by SF — always blank/null
    "last_paid_installment_date",
    "foreclosure_date",
    "disposition_date",
    "foreclosure_costs",
    "property_preservation_and_repair_costs",
    "asset_recovery_costs",
    "miscellaneous_holding_expenses_and_credits",
    "associated_taxes_for_holding_property",
    "net_sales_proceeds",
    "credit_enhancement_proceeds",
    "repurchase_make_whole_proceeds",
    "other_foreclosure_proceeds",
    "mod_related_non_interest_bearing_upb",
    "principal_forgiveness_amount",
    "original_list_start_date",  # not used by SF — always blank/null
    "original_list_price",  # not used by SF — always blank/null
    "current_list_start_date",  # not used by SF — always blank/null
    "current_list_price",  # not used by SF — always blank/null
    "borrower_credit_score_at_issuance",  # not used by SF — always blank/null
    "coborrower_credit_score_at_issuance",  # not used by SF — always blank/null
    "borrower_credit_score_current",  # not used by SF — always blank/null
    "coborrower_credit_score_current",  # not used by SF — always blank/null
    "mortgage_insurance_type",
    "servicing_activity_indicator",
    "current_period_modification_loss_amount",  # not used by SF — always blank/null
    "cumulative_modification_loss_amount",  # not used by SF — always blank/null
    "current_period_credit_event_net_gain_or_loss",  # not used by SF — always blank/null
    "cumulative_credit_event_net_gain_or_loss",  # not used by SF — always blank/null
    "special_eligibility_program",
    "foreclosure_principal_writeoff_amt",
    "relocation_mortgage_indicator",
    "zero_balance_code_change_date",  # not used by SF — always blank/null
    "loan_holdback_indicator",  # not used by SF — always blank/null
    "loan_holdback_effective_date",  # not used by SF — always blank/null
    "delinquent_accrued_interest",  # not used by SF — always blank/null
    "property_valuation_method",
    "high_balance_loan_indicator",
    "arm_initial_fixed_rate_period_le_5yr_ind",  # not used by SF — always blank/null
    "arm_product_type",  # not used by SF — always blank/null
    "initial_fixedrate_period",  # not used by SF — always blank/null
    "interest_rate_adjustment_frequency",  # not used by SF — always blank/null
    "next_interest_rate_adjustment_date",  # not used by SF — always blank/null
    "next_payment_change_date",  # not used by SF — always blank/null
    "arm_index",  # not used by SF — always blank/null
    "arm_cap_structure",  # not used by SF — always blank/null
    "initial_interest_rate_cap_up_percent",  # not used by SF — always blank/null
    "periodic_interest_rate_cap_up_percent",  # not used by SF — always blank/null
    "lifetime_interest_rate_cap_up_percent",  # not used by SF — always blank/null
    "mortgage_margin",  # not used by SF — always blank/null
    "arm_balloon_indicator",  # not used by SF — always blank/null
    "arm_plan_number",  # not used by SF — always blank/null
    "borrower_assistance_plan",
    "hltv_refinance_option_indicator",
    "deal_name",  # not used by SF — always blank/null
    "repurchase_make_whole_proceeds_flag",
    "alternative_delinquency_resolution",
    "alternative_delinquency_resolution_count",
    "total_deferral_amount",
    "payment_deferral_modification_event_indicator",
    "interest_bearing_upb",  # not used by SF — always blank/null
    "origination_classic_fico",
    "issuance_classic_fico",  # not used by SF — always blank/null
    "current_classic_fico",  # not used by SF — always blank/null
]


def load_vintage_streaming(vintage_key: str, chunksize: int = 250_000) -> None:
    """
    Stream one vintage's combined loan performance file straight into
    SQLite, chunk by chunk, instead of building one giant in-memory
    DataFrame first. These files run 3-5+ GB each — concatenating all
    chunks in memory before writing risks exhausting RAM. Each chunk
    is appended to the table directly, and progress is printed so you
    can see it's alive on a multi-GB file.
    """
    vintage = VINTAGES[vintage_key]
    path = vintage["loan_performance_file"]
    table_name = f"loan_performance_{vintage_key.lower()}"

    SQLITE_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(SQLITE_DB_PATH)

    total_rows = 0
    try:
        reader = pd.read_csv(
            path,
            sep="|",
            header=None,
            names=LOAN_PERFORMANCE_COLUMNS,
            chunksize=chunksize,
            low_memory=False,
            dtype=str,  # load everything as text — several fields (zero_balance_code,
                        # delinquency status) have meaningful leading zeros, and
                        # loan_payment_history is a 48-digit code string that
                        # overflows SQLite's INTEGER if pandas infers it numeric.
                        # Cast to numeric explicitly in SQL only where needed
                        # (e.g. loan_age for window filtering).
        )
        for i, chunk in enumerate(reader):
            # First chunk replaces any existing table; subsequent
            # chunks append, so re-running this script on a fresh
            # load doesn't duplicate rows.
            chunk.to_sql(
                table_name,
                conn,
                if_exists="replace" if i == 0 else "append",
                index=False,
            )
            total_rows += len(chunk)
            print(f"  {vintage_key}: {total_rows:,} rows written so far...")
    finally:
        conn.close()

    print(f"Loaded {vintage_key}: {total_rows:,} loan-month rows total")


if __name__ == "__main__":
    for key in VINTAGES:
        load_vintage_streaming(key)