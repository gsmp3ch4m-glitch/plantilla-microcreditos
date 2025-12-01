import sqlite3
import os

DB_PATH = 'database/system.db'

def update_schema():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print("Checking columns in loans table...")
    cursor.execute("PRAGMA table_info(loans)")
    columns = [info[1] for info in cursor.fetchall()]
    
    new_columns = {
        'sale_price': 'REAL DEFAULT 0',
        'sales_expense': 'REAL DEFAULT 0'
    }
    
    for col, dtype in new_columns.items():
        if col not in columns:
            print(f"Adding column '{col}'...")
            try:
                cursor.execute(f"ALTER TABLE loans ADD COLUMN {col} {dtype}")
                print(f"✓ Added {col}")
            except Exception as e:
                print(f"Error adding {col}: {e}")
        else:
            print(f"Column '{col}' already exists.")
            
    conn.commit()
    conn.close()

if __name__ == "__main__":
    update_schema()
