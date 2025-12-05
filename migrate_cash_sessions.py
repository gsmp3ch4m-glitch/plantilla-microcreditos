import sqlite3

def migrate():
    try:
        conn = sqlite3.connect('database/system.db')
        cursor = conn.cursor()
        
        # Check if column exists
        cursor.execute("PRAGMA table_info(cash_sessions)")
        columns = [info[1] for info in cursor.fetchall()]
        
        if 'observation' not in columns:
            print("Adding observation column...")
            cursor.execute("ALTER TABLE cash_sessions ADD COLUMN observation TEXT")
            conn.commit()
            print("Column added successfully.")
        else:
            print("Column already exists.")
            
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    migrate()
