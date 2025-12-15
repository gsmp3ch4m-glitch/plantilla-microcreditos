
from src.database import get_db_connection
from src.utils.settings_manager import update_setting

def fix_balances():
    try:
        # 1. Update Digital Balance Base (Petty Cash Setting)
        update_setting('petty_cash_balance', '1500')
        print("Updated petty_cash_balance to 1500")
        
        # 2. Update Current Session Opening Balance to 2500
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get latest open session
        cursor.execute("SELECT id FROM cash_sessions WHERE status='open' ORDER BY id DESC LIMIT 1")
        row = cursor.fetchone()
        
        if row:
            session_id = row['id']
            cursor.execute("UPDATE cash_sessions SET opening_balance = 2500 WHERE id = ?", (session_id,))
            print(f"Updated session {session_id} opening_balance to 2500")
            conn.commit()
        else:
            print("No open session found")
            
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    fix_balances()
