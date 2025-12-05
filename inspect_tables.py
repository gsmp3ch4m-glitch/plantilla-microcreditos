import sqlite3
import os

def inspect_db():
    db_path = os.path.join('database', 'system.db')
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    
    print("Tables found:")
    for table in tables:
        print(f"- {table[0]}")
        
        # Get columns for each table
        cursor.execute(f"PRAGMA table_info({table[0]})")
        columns = cursor.fetchall()
        for col in columns:
            print(f"  - {col[1]} ({col[2]})")
        print("")
        
    conn.close()

if __name__ == "__main__":
    inspect_db()
