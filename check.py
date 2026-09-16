import sqlite3
conn = sqlite3.connect("cell_counts.db")

# print("Tables:", conn.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall())
# print("Samples:", conn.execute("SELECT * FROM samples LIMIT 3;").fetchall())
# print("Cell counts:", conn.execute("SELECT * FROM cell_counts LIMIT 10;").fetchall())

print("Sample count:", conn.execute("SELECT COUNT(*) FROM samples").fetchone())
print("Cell count rows:", conn.execute("SELECT COUNT(*) FROM cell_counts").fetchone())

conn.close()