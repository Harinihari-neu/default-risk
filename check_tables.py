import sqlite3

conn = sqlite3.connect(r"data\processed\fannie_mae.db")
cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [row[0] for row in cursor.fetchall()]
print("Tables currently in database:")
for t in tables:
    print(f"  {t}")
conn.close()