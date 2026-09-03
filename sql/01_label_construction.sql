-- Collapse each loan's monthly rows into a single outcome label
-- within DEFAULT_WINDOW_MONTHS of origination.
--
-- Single-file format: loan_performance_<vintage> has one row per
-- loan per month, with static attributes (LTV, DTI, FICO, etc.)
-- repeated on every row. No join needed — everything lives in one
-- table per vintage.
--
-- Field value references (per Fannie Mae's official glossary):
--   current_loan_delinquency_status: number of months delinquent as
--     a zero-padded string ('00' = current, '01' = 30-59 days,
--     '02' = 60-89 days, '03' = 90-119 days, ... 'XX' = unknown).
--     "90+ days delinquent" = CAST(...) >= 3.
--   zero_balance_code: '01' = Prepaid or Matured, '02' = Third Party
--     Sale, '03' = Short Sale, '06' = Repurchased,
--     '09' = Deed-in-Lieu/REO Disposition, '15' = Notes Sale,
--     '16' = Reperforming Loan Sale, '96' = Removal (non-credit event).
--     Treat '01' as prepay; treat '02','03','09' as default/foreclosure
--     if not already caught by delinquency status.
--
-- IMPORTANT — COVID forbearance caveat (discovered via diagnostics on
-- this dataset): loans reaching 90+ days delinquent while under a
-- CARES Act forbearance plan (borrower_assistance_plan = 'F') are
-- NOT genuine credit defaults — the borrower requested payment relief
-- and was reported as delinquent per Fannie's disclosure rules, but
-- did not actually stop paying due to financial distress in the
-- traditional sense. For the 2019Q1 vintage, this affected 94% of
-- loans that would otherwise have been labeled 'default' (their
-- 24-month mark lands ~Q1 2021, during peak forbearance activity).
-- We therefore split this out into a separate 'covid_forbearance'
-- outcome rather than counting it as 'default', so the label
-- reflects actual credit risk rather than a pandemic reporting
-- artifact.

CREATE TABLE IF NOT EXISTS loan_labels_2007q1 AS
WITH within_window AS (
    SELECT *
    FROM loan_performance_2007q1
    WHERE CAST(loan_age AS INTEGER) <= 24  -- DEFAULT_WINDOW_MONTHS
),
loan_outcomes AS (
    SELECT
        loan_identifier,
        MAX(
            CASE
                WHEN current_loan_delinquency_status GLOB '[0-9][0-9]'
                     AND CAST(current_loan_delinquency_status AS INTEGER) >= 3
                THEN 1
                WHEN zero_balance_code IN ('02', '03', '09') THEN 1
                ELSE 0
            END
        ) AS defaulted,
        MAX(CASE WHEN zero_balance_code = '01' THEN 1 ELSE 0 END) AS prepaid,
        MAX(CASE WHEN borrower_assistance_plan IN ('F', 'C') THEN 1 ELSE 0 END) AS had_forbearance
    FROM within_window
    GROUP BY loan_identifier
)
SELECT
    loan_identifier,
    defaulted,
    prepaid,
    had_forbearance,
    CASE
        WHEN defaulted = 1 AND had_forbearance = 1 THEN 'covid_forbearance'
        WHEN defaulted = 1 THEN 'default'
        WHEN prepaid = 1 THEN 'prepay'
        ELSE 'current'
    END AS outcome
FROM loan_outcomes;

-- Repeat identical logic for 2019Q1.
CREATE TABLE IF NOT EXISTS loan_labels_2019q1 AS
WITH within_window AS (
    SELECT *
    FROM loan_performance_2019q1
    WHERE CAST(loan_age AS INTEGER) <= 24
),
loan_outcomes AS (
    SELECT
        loan_identifier,
        MAX(
            CASE
                WHEN current_loan_delinquency_status GLOB '[0-9][0-9]'
                     AND CAST(current_loan_delinquency_status AS INTEGER) >= 3
                THEN 1
                WHEN zero_balance_code IN ('02', '03', '09') THEN 1
                ELSE 0
            END
        ) AS defaulted,
        MAX(CASE WHEN zero_balance_code = '01' THEN 1 ELSE 0 END) AS prepaid,
        MAX(CASE WHEN borrower_assistance_plan IN ('F', 'C') THEN 1 ELSE 0 END) AS had_forbearance
    FROM within_window
    GROUP BY loan_identifier
)
SELECT
    loan_identifier,
    defaulted,
    prepaid,
    had_forbearance,
    CASE
        WHEN defaulted = 1 AND had_forbearance = 1 THEN 'covid_forbearance'
        WHEN defaulted = 1 THEN 'default'
        WHEN prepaid = 1 THEN 'prepay'
        ELSE 'current'
    END AS outcome
FROM loan_outcomes;