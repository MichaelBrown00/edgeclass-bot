import sqlite3

conn = sqlite3.connect("edgeclass.db")
cur = conn.cursor()

try:
    cur.execute("ALTER TABLE users ADD COLUMN plan TEXT DEFAULT 'free'")
    conn.commit()
    print("✅ plan column added.")
except Exception as e:
    print(e)

cur.execute("PRAGMA table_info(users)")
print(cur.fetchall())

conn.close()