import sqlite3
from src.database_sqlite import init_db, get_db_connection

def verify_manual_receivables():
    print("Initializing DB...")
    init_db()
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    print("Checking manual_receivables table...")
    try:
        cursor.execute("SELECT * FROM manual_receivables")
        print("Table exists.")
    except sqlite3.OperationalError:
        print("Table DOES NOT exist. Creating...")
        # Should be created by init_db
        return
        
    print("Inserting test manual debt...")
    cursor.execute("""
        INSERT INTO manual_receivables (client_name, concept, amount_lent, interest, total_debt, paid_amount, balance)
        VALUES ('Juan Perez Test', 'Deuda Antigua', 1000, 100, 1100, 100, 1000)
    """)
    mid = cursor.lastrowid
    conn.commit()
    print(f"Inserted ID: {mid}")
    
    print("Querying inserted data...")
    cursor.execute("SELECT * FROM manual_receivables WHERE id=?", (mid,))
    row = cursor.fetchone()
    print(f"Row: {dict(row)}")
    
    # Clean up
    cursor.execute("DELETE FROM manual_receivables WHERE id=?", (mid,))
    conn.commit()
    conn.close()
    print("Verification complete.")

if __name__ == "__main__":
    verify_manual_receivables()
