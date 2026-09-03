import sqlite3

conn = sqlite3.connect(r"data\processed\fannie_mae.db")

print("=== Distinct zero_balance_code values actually present (2007Q1) ===")
for row in conn.execute(
    "SELECT zero_balance_code, COUNT(*) FROM loan_performance_2007q1 GROUP BY zero_balance_code ORDER BY COUNT(*) DESC LIMIT 15"
):
    print(f"  {row[0]!r:10s} {row[1]:>10,}")

print("\n=== Distinct current_loan_delinquency_status values (2007Q1, sample) ===")
for row in conn.execute(
    "SELECT current_loan_delinquency_status, COUNT(*) FROM loan_performance_2007q1 GROUP BY current_loan_delinquency_status ORDER BY COUNT(*) DESC LIMIT 15"
):
    print(f"  {row[0]!r:10s} {row[1]:>10,}")

print("\n=== Max delinquency status reached within 24mo window, by vintage ===")
for row in conn.execute(
    """
    SELECT
        '2007Q1' as vintage,
        MAX(CASE WHEN current_loan_delinquency_status GLOB '[0-9][0-9]'
                 THEN CAST(current_loan_delinquency_status AS INTEGER) END) as max_dlq
    FROM loan_performance_2007q1
    WHERE CAST(loan_age AS INTEGER) <= 24
    """
):
    print(f"  {row}")

print("\n=== Borrower assistance plan codes present in 2019Q1 defaults (COVID forbearance check) ===")
for row in conn.execute(
    """
    SELECT p.borrower_assistance_plan, COUNT(DISTINCT p.loan_identifier)
    FROM loan_performance_2019q1 p
    JOIN loan_labels_2019q1 l ON p.loan_identifier = l.loan_identifier
    WHERE l.outcome = 'default'
    GROUP BY p.borrower_assistance_plan
    ORDER BY COUNT(DISTINCT p.loan_identifier) DESC
    """
):
    print(f"  {row[0]!r:10s} {row[1]:>10,}")

conn.close()