
import sqlite3
import os

def fix_balances_direct():
    db_path = os.path.join(os.getcwd(), 'database', 'system.db')
    print(f"Connecting to {db_path}")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # 1. Update Settings 'petty_cash_balance' to 1500
        # Check if setting exists
        cursor.execute("SELECT key FROM settings WHERE key = 'petty_cash_balance'")
        if cursor.fetchone():
            cursor.execute("UPDATE settings SET value = '1500' WHERE key = 'petty_cash_balance'")
        else:
            cursor.execute("INSERT INTO settings (key, value) VALUES ('petty_cash_balance', '1500')")
        print("Updated settings: petty_cash_balance = 1500")

        # 2. Update Session Opening Balance to 2500
        cursor.execute("SELECT id FROM cash_sessions WHERE status='open' ORDER BY id DESC LIMIT 1")
        row = cursor.fetchone()
        if row:
            sess_id = row[0]
            cursor.execute("UPDATE cash_sessions SET opening_balance = 2500 WHERE id = ?", (sess_id,))
            print(f"Updated Session {sess_id} opening_balance to 2500")
        else:
            print("No open session found.")

        conn.commit()
        print("Commit successful.")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    fix_balances_direct()
