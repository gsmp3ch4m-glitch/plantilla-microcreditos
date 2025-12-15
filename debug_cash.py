
from src.database import get_db_connection
import json

def debug_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. Check Cash Session
    cursor.execute("SELECT * FROM cash_sessions ORDER BY id DESC LIMIT 1")
    session = cursor.fetchone()
    session_data = dict(session) if session else None
    
    # 2. Check Transactions for this session (if exists)
    transactions = []
    if session_data:
        cursor.execute("SELECT id, type, amount, payment_method FROM transactions WHERE cash_session_id = ?", (session_data['id'],))
        transactions = [dict(r) for r in cursor.fetchall()]

    # 3. Check Capital Entries
    cursor.execute("SELECT * FROM capital_entries ORDER BY id DESC LIMIT 5")
    capital = [dict(r) for r in cursor.fetchall()]

    report = {
        'session': session_data,
        'transactions': transactions,
        'capital': capital
    }
    
    with open("debug_report.json", "w") as f:
        json.dump(report, f, indent=2, default=str)
        
    conn.close()

if __name__ == "__main__":
    debug_db()
