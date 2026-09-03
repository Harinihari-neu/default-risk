import sqlite3

conn = sqlite3.connect(r"data\processed\fannie_mae.db")

print("=== Row counts by vintage ===")
for row in conn.execute("SELECT vintage, COUNT(*) FROM training_data GROUP BY vintage"):
    print(f"  {row[0]}: {row[1]:,} loans")

print("\n=== Outcome breakdown by vintage ===")
for row in conn.execute(
    "SELECT vintage, outcome, COUNT(*) FROM training_data GROUP BY vintage, outcome ORDER BY vintage, outcome"
):
    print(f"  {row[0]:8s} {row[1]:10s} {row[2]:>10,}")

print("\n=== Default rate by vintage ===")
for row in conn.execute(
    """
    SELECT
        vintage,
        COUNT(*) AS total,
        SUM(CASE WHEN outcome = 'default' THEN 1 ELSE 0 END) AS defaults,
        ROUND(100.0 * SUM(CASE WHEN outcome = 'default' THEN 1 ELSE 0 END) / COUNT(*), 2) AS default_rate_pct
    FROM training_data
    GROUP BY vintage
    """
):
    print(f"  {row[0]:8s} total={row[1]:>10,}  defaults={row[2]:>8,}  default_rate={row[3]}%")

print("\n=== Sample rows ===")
for row in conn.execute("SELECT * FROM training_data LIMIT 3"):
    print(row)

conn.close()