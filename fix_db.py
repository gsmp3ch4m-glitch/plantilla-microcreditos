import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), 'src', 'database', 'system.db')
if not os.path.exists(DB_PATH):
    # Try alternate path if running from root
    DB_PATH = os.path.join(os.path.dirname(__file__), 'database', 'system.db')

print(f"Checking database at: {DB_PATH}")

def fix_database():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Check loans table columns
    cursor.execute("PRAGMA table_info(loans)")
    columns = [info[1] for info in cursor.fetchall()]
    print(f"Current columns in loans: {columns}")
    
    if 'due_date' not in columns:
        print("Adding missing column 'due_date'...")
        try:
            cursor.execute("ALTER TABLE loans ADD COLUMN due_date DATE")
            print("✓ Column 'due_date' added successfully.")
        except Exception as e:
            print(f"Error adding column: {e}")
    else:
        print("Column 'due_date' already exists.")
        
    # Check pawn_details table columns
    cursor.execute("PRAGMA table_info(pawn_details)")
    pawn_columns = [info[1] for info in cursor.fetchall()]
    print(f"Current columns in pawn_details: {pawn_columns}")
    
    # List of expected columns for pawn_details
    expected_pawn_cols = {
        'item_type': 'TEXT',
        'brand': 'TEXT',
        'characteristics': 'TEXT',
        'condition': 'TEXT',
        'market_value': 'REAL'
    }
    
    for col, dtype in expected_pawn_cols.items():
        if col not in pawn_columns:
            print(f"Adding missing column '{col}' to pawn_details...")
            try:
                cursor.execute(f"ALTER TABLE pawn_details ADD COLUMN {col} {dtype}")
                print(f"✓ Column '{col}' added successfully.")
            except Exception as e:
                print(f"Error adding column {col}: {e}")
        else:
            print(f"Column '{col}' already exists in pawn_details.")

    conn.commit()
    conn.close()

if __name__ == "__main__":
    fix_database()
