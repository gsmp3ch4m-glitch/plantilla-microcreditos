import sqlite3
from src.database_sqlite import init_db, get_db_connection

def verify_enhanced_receivables():
    print("Initializing DB...")
    init_db()
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. Verify Columns
    print("Checking manual_receivables columns...")
    cursor.execute("PRAGMA table_info(manual_receivables)")
    columns = [row['name'] for row in cursor.fetchall()]
    print(f"Columns: {columns}")
    
    required = ['client_id', 'modality', 'loan_date', 'due_date']
    missing = [col for col in required if col not in columns]
    if missing:
        print(f"ERROR: Missing columns: {missing}")
    else:
        print("All new columns present.")
        
    # 2. Test Insert with new fields
    print("Testing Insert...")
    try:
        cursor.execute("""
            INSERT INTO manual_receivables (client_name, client_id, concept, modality, amount_lent, interest, 
                                           total_debt, paid_amount, balance, status, loan_date, due_date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, ('Test Client', None, 'Test Concept', 'Rapidiario', 1000, 100, 1100, 0, 1100, 'pending', '2025-12-13', '2025-12-20'))
        mid = cursor.lastrowid
        conn.commit()
        print(f"Inserted ID: {mid}")
        
        cursor.execute("SELECT * FROM manual_receivables WHERE id=?", (mid,))
        row = dict(cursor.fetchone())
        print(f"Row: {row}")
        
        # Clean up
        cursor.execute("DELETE FROM manual_receivables WHERE id=?", (mid,))
        conn.commit()
    except Exception as e:
        print(f"INSERT ERROR: {e}")
        
    conn.close()
    print("Verification complete.")

if __name__ == "__main__":
    verify_enhanced_receivables()
