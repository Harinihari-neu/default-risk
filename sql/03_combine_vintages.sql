-- Combine both vintages into the single training table modeling
-- notebooks will read from. Run this after 01_label_construction.sql
-- and 02_feature_table.sql have built features_2007q1 and
-- features_2019q1.

CREATE TABLE IF NOT EXISTS training_data AS
SELECT * FROM features_2007q1
UNION ALL
SELECT * FROM features_2019q1;

-- Quick sanity checks — run these manually after building the table:
--   SELECT vintage, COUNT(*) FROM training_data GROUP BY vintage;
--   SELECT vintage, outcome, COUNT(*) FROM training_data GROUP BY vintage, outcome;