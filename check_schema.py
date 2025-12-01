import sqlite3
import os

DB_PATH = 'database/system.db'

def dump_schema():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    with open('schema_dump_utf8.txt', 'w', encoding='utf-8') as f:
        f.write("--- Loans Table ---\n")
        cursor.execute("PRAGMA table_info(loans)")
        for col in cursor.fetchall():
            f.write(str(col) + "\n")
            
        f.write("\n--- Settings Table ---\n")
        cursor.execute("PRAGMA table_info(settings)")
        for col in cursor.fetchall():
            f.write(str(col) + "\n")

    conn.close()

if __name__ == "__main__":
    dump_schema()
