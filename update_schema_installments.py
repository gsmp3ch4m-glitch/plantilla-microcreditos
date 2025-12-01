import sqlite3
import os

DB_PATH = 'database/system.db'

def update_schema():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print("Checking columns in installments table...")
    cursor.execute("PRAGMA table_info(installments)")
    columns = [info[1] for info in cursor.fetchall()]
    
    if 'amount_paid' not in columns:
        print("Adding column 'amount_paid'...")
        try:
            cursor.execute("ALTER TABLE installments ADD COLUMN amount_paid REAL DEFAULT 0")
            print("✓ Added amount_paid")
        except Exception as e:
            print(f"Error adding amount_paid: {e}")
    else:
        print("Column 'amount_paid' already exists.")
            
    conn.commit()
    conn.close()

if __name__ == "__main__":
    update_schema()
