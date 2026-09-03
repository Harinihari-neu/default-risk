# Decisions log

Running record of choices made on this project, so the "why" behind
the repo is visible later (and reusable for the interview narrative).

## 2026-09-03 — Project kickoff

- **Vintages**: 2007 Q1 (crisis-era) and 2019 Q1 (stable-era) —
  chosen for contrast in realized default rates.
- **SQL engine**: SQLite, not Postgres. Data volume (1-2 quarters)
  doesn't need a server DB; SQLite is zero-setup and the interview
  story ("loaded raw files, wrote SQL joins/aggregations") is
  identical either way.
- **Loading approach**: Python script (pandas -> SQLite) rather than
  SQLite's native `.import`. Raw files have no headers and need type
  coercion / null handling (e.g. sentinel values like 9999 for
  missing FICO) — easier to control in pandas, and it's reusable,
  demonstrable code.
- **Default window**: 24 months from origination.
- **Default definition**: 90+ days delinquent OR foreclosure within
  the window (exact status code mapping TBD from glossary).

## 2026-09-03 — Single-file format confirmed

- Fannie Mae's SF Loan Performance data is distributed as **one
  combined file per vintage quarter** (one row per loan per month;
  static origination attributes like LTV/DTI/FICO are repeated on
  every monthly row), not as separate acquisition + performance
  files as originally assumed.
- Updated `config.py`, `load_data.py`, and both SQL scripts
  accordingly: no join between two files needed — the feature table
  is built by taking one static snapshot per loan (earliest
  `loan_age`) and aggregating monthly rows for the outcome label,
  all from a single table per vintage.
- Field list in `LOAN_PERFORMANCE_COLUMNS` (in `load_data.py`) is
  provisional — sourced from a combined CAS/CIRT/SF glossary where
  position numbers were non-contiguous for SF alone. Needs
  verification against the SF-specific glossary before running.

## 2026-09-04 — Column layout verified

- Confirmed the actual downloaded file has exactly 113 pipe-delimited
  columns (`(Get-Content .\2007Q1.csv -TotalCount 1) -split '\|' |
  Measure-Object` → 113), matching Fannie Mae's official combined
  CAS/CIRT/SF "Glossary and File Layout" (113 field positions).
  Fields not applicable to SF are still present as columns — always
  blank/null for SF data.
- `LOAN_PERFORMANCE_COLUMNS` in `load_data.py` now reflects this
  verified, exact order (snake_case names derived from the official
  field names, a few shortened for usability — e.g. `orig_ltv`,
  `dti`, `msa`).
- Delinquency/default definition finalized:
  `current_loan_delinquency_status` >= '03' (90+ days) OR
  `zero_balance_code` IN ('02','03','09') (third-party sale, short
  sale, deed-in-lieu/REO) counts as default. `zero_balance_code =
  '01'` (prepaid or matured) counts as prepay.
- Updated `sql/01_label_construction.sql` and `sql/02_feature_table.sql`
  to use real column names and these enumerations — no more
  placeholder TODOs.

## 2026-09-04 — Streaming loader (files are much larger than expected)

- Actual downloaded files are large: 2007Q1.csv ≈ 4.5 GB, 2019Q1.csv
  ≈ 3.5 GB (~8 GB total). Rewrote `load_data.py` to stream each chunk
  straight into SQLite (`if_exists="append"` after the first chunk)
  instead of concatenating the whole file into memory first — the
  previous approach would likely have exhausted RAM on files this
  size.
- Loader now prints running row-count progress per chunk so long
  loads are visibly alive rather than silent.

## Open / next decisions

- Run `load_data.py` against actual 2007Q1/2019Q1 files and confirm
  row counts / spot-check a few loans against the raw text.
- Decide feature set beyond current list — e.g. add MSA, zip3,
  amortization type, prepayment penalty indicator?
