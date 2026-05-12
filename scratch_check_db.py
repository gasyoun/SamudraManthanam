import sqlite3
import os

db_path = "web/corpus.db"
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT title, sha256, size FROM sources LIMIT 5")
        rows = cursor.fetchall()
        print("First 5 sources:")
        for row in rows:
            print(f"Title: {row[0]}, SHA: {row[1]}, Size: {row[2]}")
    except Exception as e:
        print(f"Error: {e}")
    conn.close()
else:
    print(f"{db_path} not found.")
