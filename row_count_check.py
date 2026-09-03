import sqlite3

conn = sqlite3.connect(r"data\processed\fannie_mae.db")

for table in ["loan_performance_2007q1", "loan_performance_2019q1"]:
    count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
    print(f"{table}: {count:,} rows")

conn.close()