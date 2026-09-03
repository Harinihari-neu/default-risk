import sqlite3

conn = sqlite3.connect(r"data\processed\fannie_mae.db")

tables = [
    "training_data",
    "features_2007q1",
    "features_2019q1",
    "loan_labels_2007q1",
    "loan_labels_2019q1",
    "loan_performance_2007q1",
    "loan_performance_2019q1",
]

for t in tables:
    conn.execute(f"DROP TABLE IF EXISTS {t}")
    print(f"Dropped {t} (if it existed)")

conn.commit()
conn.close()
print("\nDatabase reset — ready for a clean reload.")