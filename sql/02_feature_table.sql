-- Build the final one-row-per-loan training table: static
-- origination attributes (taken from the earliest reported month per
-- loan, since they're repeated on every monthly row) joined to the
-- outcome label built in 01_label_construction.sql.
--
-- Uses ROW_NUMBER() OVER (PARTITION BY loan_identifier ORDER BY
-- loan_age) instead of a correlated subquery (SELECT MIN(loan_age)
-- WHERE loan_identifier = ...) — the correlated version rescans the
-- whole table per row and is extremely slow on 10M+ row tables. The
-- window-function version does one sorted pass.
--
-- Run sql/00_create_indexes.sql first if you haven't already.

-- Drop any partial tables from a previous interrupted run before
-- rebuilding — CREATE TABLE IF NOT EXISTS would otherwise silently
-- skip recreating a table that was only half-written.
DROP TABLE IF EXISTS features_2007q1;

CREATE TABLE features_2007q1 AS
WITH ranked AS (
    SELECT
        p.*,
        ROW_NUMBER() OVER (
            PARTITION BY p.loan_identifier
            ORDER BY CAST(p.loan_age AS INTEGER) ASC
        ) AS rn
    FROM loan_performance_2007q1 p
)
SELECT
    r.loan_identifier,
    CAST(r.borrower_credit_score AS INTEGER) AS borrower_credit_score,
    CAST(r.orig_ltv AS INTEGER) AS orig_ltv,
    CAST(r.orig_cltv AS INTEGER) AS orig_cltv,
    CAST(r.dti AS INTEGER) AS dti,
    r.loan_purpose,
    r.occupancy_status,
    r.property_type,
    r.property_state,
    CAST(r.number_of_units AS INTEGER) AS number_of_units,
    CAST(r.number_of_borrowers AS INTEGER) AS number_of_borrowers,
    r.first_time_home_buyer_indicator,
    CAST(r.original_loan_term AS INTEGER) AS original_loan_term,
    CAST(r.original_interest_rate AS REAL) AS original_interest_rate,
    r.amortization_type,
    CAST(r.mortgage_insurance_percentage AS REAL) AS mortgage_insurance_percentage,
    l.outcome,
    '2007Q1' AS vintage
FROM ranked r
JOIN loan_labels_2007q1 l ON r.loan_identifier = l.loan_identifier
WHERE r.rn = 1;

-- Repeat identical logic for 2019Q1.
DROP TABLE IF EXISTS features_2019q1;

CREATE TABLE features_2019q1 AS
WITH ranked AS (
    SELECT
        p.*,
        ROW_NUMBER() OVER (
            PARTITION BY p.loan_identifier
            ORDER BY CAST(p.loan_age AS INTEGER) ASC
        ) AS rn
    FROM loan_performance_2019q1 p
)
SELECT
    r.loan_identifier,
    CAST(r.borrower_credit_score AS INTEGER) AS borrower_credit_score,
    CAST(r.orig_ltv AS INTEGER) AS orig_ltv,
    CAST(r.orig_cltv AS INTEGER) AS orig_cltv,
    CAST(r.dti AS INTEGER) AS dti,
    r.loan_purpose,
    r.occupancy_status,
    r.property_type,
    r.property_state,
    CAST(r.number_of_units AS INTEGER) AS number_of_units,
    CAST(r.number_of_borrowers AS INTEGER) AS number_of_borrowers,
    r.first_time_home_buyer_indicator,
    CAST(r.original_loan_term AS INTEGER) AS original_loan_term,
    CAST(r.original_interest_rate AS REAL) AS original_interest_rate,
    r.amortization_type,
    CAST(r.mortgage_insurance_percentage AS REAL) AS mortgage_insurance_percentage,
    l.outcome,
    '2019Q1' AS vintage
FROM ranked r
JOIN loan_labels_2019q1 l ON r.loan_identifier = l.loan_identifier
WHERE r.rn = 1;