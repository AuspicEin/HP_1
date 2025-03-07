import sqlite3

def update_db():
    with sqlite3.connect("database.db") as conn:
        try:
            conn.execute("ALTER TABLE urls ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
            print("カラム `created_at` を追加しました。")
        except sqlite3.OperationalError:
            print("`created_at` カラムは既に存在します。")

update_db()
