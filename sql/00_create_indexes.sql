-- Indexes to speed up the label/feature construction queries.
-- Run this BEFORE 01_label_construction.sql and 02_feature_table.sql.
-- Without these, GROUP BY / JOIN / correlated-subquery operations on
-- 16M+ row tables force full table scans repeatedly.

CREATE INDEX IF NOT EXISTS idx_perf_2007q1_loan_id
    ON loan_performance_2007q1(loan_identifier);

CREATE INDEX IF NOT EXISTS idx_perf_2019q1_loan_id
    ON loan_performance_2019q1(loan_identifier);