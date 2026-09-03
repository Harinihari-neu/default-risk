# Raw data (not committed)

This folder holds the original Fannie Mae files. They're excluded
from git via `.gitignore` because they're large and freely
re-downloadable — no reason to bloat the repo.

## How to get them

1. Register for a free account at the
   [Fannie Mae Data Dynamics portal](https://datadynamics.fanniemae.com/).
2. Navigate to the **Single-Family Loan Performance Dataset**.
3. Download the acquisition and performance files for:
   - **2007 Q1**
   - **2019 Q1**
4. Also download the **file layout / glossary PDF** from the same
   page — the raw files have no header row, and column definitions
   have changed across vintages.

## Expected files in this folder

Fannie Mae distributes SF Loan Performance data as a single combined
file per vintage quarter (one row per loan per month; static
origination attributes are repeated on every monthly row):

```
data/raw/
  2007Q1.csv
  2019Q1.csv
  glossary/
    sf_file_layout_and_glossary.pdf
```

(Exact filenames depend on what the portal names the download —
rename to match the above so the loading scripts in `src/` work
without edits, or update the paths in `src/config.py`.)

## Format notes

- Pipe-delimited (`|`), no header row.
- Column order and names come from the glossary PDF — see
  `docs/data_dictionary.md` once populated for the transcribed
  column list used in this project.
- Missing/sentinel values vary by field (e.g. FICO scores use `9999`
  for missing) — handled in `src/load_data.py`.
