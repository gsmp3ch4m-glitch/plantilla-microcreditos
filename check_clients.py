import sqlite3
from src.database_sqlite import get_db_connection

def check():
    conn = get_db_connection()
    try:
        rows = conn.execute("SELECT * FROM clients").fetchall()
        print(f"Total clients: {len(rows)}")
        for r in rows:
            print(f"{r['first_name']} {r['last_name']} - {r['dni']}")
    except Exception as e:
        print(e)
    conn.close()

if __name__ == "__main__":
    check()
