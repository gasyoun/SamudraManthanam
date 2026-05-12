import sqlite3
import os

db_path = "web/corpus.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()
cursor.execute("SELECT title FROM sources LIMIT 5")
rows = cursor.fetchall()
with open("db_titles.txt", "w", encoding="utf-8") as f:
    for row in rows:
        f.write(row[0] + "\n")
conn.close()
print("Titles written to db_titles.txt")
