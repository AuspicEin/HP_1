import sqlite3

with sqlite3.connect("database.db") as conn:
    cur = conn.cursor()
    cur.execute("PRAGMA table_info(urls)")
    columns = cur.fetchall()

for col in columns:
    print(col)
