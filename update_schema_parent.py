import sqlite3
import os

DB_PATH = 'database/system.db'

def update_schema():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print("Checking columns in loans table...")
    cursor.execute("PRAGMA table_info(loans)")
    columns = [info[1] for info in cursor.fetchall()]
    
    if 'parent_loan_id' not in columns:
        print("Adding column 'parent_loan_id'...")
        try:
            cursor.execute("ALTER TABLE loans ADD COLUMN parent_loan_id INTEGER")
            print("✓ Added parent_loan_id")
        except Exception as e:
            print(f"Error adding parent_loan_id: {e}")
    else:
        print("Column 'parent_loan_id' already exists.")
            
    conn.commit()
    conn.close()

if __name__ == "__main__":
    update_schema()
